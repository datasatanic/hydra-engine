import logging
import os
import json
import uuid
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette_prometheus import metrics, PrometheusMiddleware

from hydra_engine import router
from hydra_engine.parser import parse_config_files
from hydra_engine.schemas import add_node, tree, add_additional_fields
from hydra_engine.search.index_schema import HydraIndexScheme
from hydra_engine.search.searcher import HydraSearcher

logger = logging.getLogger("common_logger")
base_dir = os.path.dirname(os.path.abspath(__file__))
app_static = FastAPI()

app_static.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app_static.add_middleware(PrometheusMiddleware)

app_static.get("/metrics", name='metrics')(metrics)
app = FastAPI()
app.include_router(router=router.router)

app_static.mount("/api", app, "hydra_engine_api")
templates = Jinja2Templates(directory="hydra_engine/static")


@app_static.get('/health')
async def stats():
    return {'service': 'hydra-engine', 'status': 'Serve'}


@app_static.get("/hydra_engine/static/{url:path}", response_class=FileResponse)
def get_template_statics(url: str):
    for root, dirs, files in os.walk("/code/hydra_engine/static"):
        for file in files:
            if os.path.join(root, file) == os.path.join("/code/hydra_engine/static", url):
                return os.path.join(root, file)


@app_static.on_event("startup")
async def startup_event():
    logger.debug("Start parsing directory")
    try:
        parse_config_files()
        read_controls_file("files")
        logger.debug("Directory has been parsed successfully")
    except Exception as e:
        logger.error(f"Error in parsing files with {e}")
    await HydraSearcher(index_name="HYDRA", schema=HydraIndexScheme()).reindex_hydra()


@app_static.get("/testapi", response_class=HTMLResponse)
async def set_values(request: Request):
    for root, dirs, files in os.walk("files"):
        for name in files:
            if name == "test.json" and "terragrunt-cache" not in root:
                with open(os.path.join(root, name)) as file:
                    plan = json.load(file)
    return templates.TemplateResponse("plan.html",
                                      {"request": request, "plan": {"plan": find_changes_in_terraform_plan(plan)},
                                       "id": uuid})


app_static.mount("/", StaticFiles(directory="wwwroot", html=True), "client")


def read_controls_file(directory):
    """
        Reads meta file of tree and creates structured tree
    """
    input_url_pattern = r'^[a-zA-Z0-9_/\\.-]+:$'
    display_name_pattern = r"\s*display_name:\s*[\"'].*[\"']"
    description_pattern = r"\s*description:\s*[\"'].*[\"']"
    tree.clear()
    path = ""
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == "controls.meta" and "terragrunt-cache" not in root:
                try:
                    f = open(os.path.join(root, name))
                    for line in f:
                        str_list = list(filter(lambda x: len(x), line.replace('\n', '').strip().split(":")))
                        if line != '\n':
                            if re.match(input_url_pattern, line.strip()):
                                path = str_list[0]
                                add_node(path.split("/"))
                            else:
                                description_match = re.match(description_pattern, line)
                                display_name_match = re.match(display_name_pattern, line)
                                if description_match or display_name_match:
                                    add_additional_fields(path.split("/"), str_list)
                                else:
                                    raise ValueError(f"Not valid line {line.strip()}")
                    break
                except Exception as e:
                    logger.error(f"Error in parsing 'controls.meta' {e}")
                    return


def find_changes_in_terraform_plan(plan_dict):
    resource_changes = plan_dict["resource_changes"]
    changes_dict = {}
    for resource in resource_changes:
        resource_address = resource["address"]
        changes_dict[resource_address] = {"old": {}, "new": {}}
        change_after = resource.get("change").get("after")
        change_after_unknown = resource.get("change").get("after_unknown")
        change_before = resource.get("change").get("before")
        change_actions = resource.get("change").get("actions")
        if "no-op" not in change_actions:
            for key, value in change_before.items():
                new_value = None
                old_value = value
                if key in change_after:
                    new_value = change_after.get(key)
                if key not in change_after and key in change_after_unknown:
                    changes_dict[resource_address]["old"][key] = old_value
                    changes_dict[resource_address]["new"][key] = "known after apply"
                elif old_value != new_value and (
                        new_value is not None and new_value != "" or old_value is not None and old_value != ""):
                    changes_dict[resource_address]["old"][key] = old_value
                    changes_dict[resource_address]["new"][key] = new_value
            for key, value in change_after.items():
                if key not in change_before:
                    new_value = value
                    changes_dict[resource_address]["new"][key] = new_value
        else:
            for key, value in change_before.items():
                changes_dict[resource_address]["old"][key] = value
        resource[resource_address] = {"actions": change_actions, "values_change": changes_dict[resource_address]}
        resource.pop("change")
        resource.pop("address")
        for key in list(resource):
            if key != resource_address:
                resource[resource_address][key] = resource[key]
                resource.pop(key)
    return plan_dict
