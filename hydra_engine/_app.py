import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

import ruamel.yaml
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette_prometheus import metrics, PrometheusMiddleware

from schemas import Condition
from hydra_engine import router, wizard_router, filewatcher
from hydra_engine.configs import config
from hydra_engine.parser import parse_config_files
from hydra_engine.schemas import add_node, HydraParametersInfo, add_additional_fields
from hydra_engine.search.index_schema import HydraIndexScheme
from hydra_engine.search.searcher import HydraSearcher

yaml = ruamel.yaml.YAML(typ="rt")
logger = logging.getLogger("common_logger")
base_dir = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def startup_event(app: FastAPI):
    logger.debug("Start parsing directory")
    parse_config_files()
    read_ui_file(os.path.join(base_dir, "files"))
    generate_wizard_meta(os.path.join(base_dir, "files/frameworks/arch"))
    read_wizard_file(os.path.join(base_dir, "files"))
    HydraParametersInfo().set_modify_time()
    logger.debug("Directory has been parsed successfully")
    await HydraSearcher(index_name="HYDRA", schema=HydraIndexScheme()).reindex_hydra()
    filewatcher.start_monitoring_files()
    yield


app_static = FastAPI(lifespan=startup_event)

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
app.include_router(router=wizard_router.router)
app_static.mount("/api", app, "hydra_engine_api")
templates = Jinja2Templates(directory="hydra_engine/static")


@app_static.get('/health')
async def stats():
    return {'service': 'hydra-engine', 'status': 'Serve'}


app_static.mount("/", StaticFiles(directory=os.path.join(base_dir, "wwwroot"), html=True), "client")


def read_ui_file(directory):
    """
        Reads meta file of tree and creates structured tree
    """
    HydraParametersInfo().tree.clear()
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == config.tree_filename:
                with open(os.path.join(root, name), 'r') as stream:
                    data_loaded = yaml.load(stream)
                    for obj in data_loaded:
                        path = obj.split("/")
                        add_node(path, data_loaded[obj]["id"], data_loaded[obj]["type"])
                        add_additional_fields(path, "display_name", data_loaded[obj]["display_name"])
                        if "description" in data_loaded[obj]:
                            add_additional_fields(path, "description", data_loaded[obj]["description"])


def read_wizard_file(directory):
    """
        Reads meta file of wizard tree and creates structured tree
    """
    HydraParametersInfo().wizard_tree.clear()
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == config.wizard_filename:
                with open(os.path.join(root, name), 'r') as stream:
                    data_loaded = yaml.load(stream)
                    for obj in data_loaded:
                        path = obj.split("/")
                        condition_list = []
                        if "condition" in data_loaded[obj]:
                            condition_data = data_loaded[obj]["condition"]
                            for condition in condition_data:
                                for key in condition:
                                    condition_schema = Condition(key=key, allow=condition[key])
                                    condition_list.append(condition_schema)
                        add_node(path, data_loaded[obj]["id"], data_loaded[obj]["type"], condition=condition_list,
                                 is_wizard=True)
                        add_additional_fields(path, "display_name", data_loaded[obj]["display_name"], is_wizard=True)
                        if "description" in data_loaded[obj]:
                            add_additional_fields(path, "description", data_loaded[obj]["description"], is_wizard=True)
                        if "action" in data_loaded[obj]:
                            add_additional_fields(path, "action", data_loaded[obj]["action"], is_wizard=True)
                        if "site_name" in data_loaded[obj]:
                            add_additional_fields(path, "site_name", data_loaded[obj]["site_name"], is_wizard=True)


def generate_wizard_meta(directory):
    file = open(os.path.join(base_dir, "files/wizard.meta"), 'r+')
    wizard_data = yaml.load(file)
    last_id = None
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name.endswith("meta"):
                last_key, last_value = list(wizard_data.items())[-1]
                if last_id is None:
                    last_id = last_value["id"]
                else:
                    last_id += 1
                wizard_form = {f"root/{name.replace('.yml.meta', '')}": {"display_name": name.replace('.yml.meta', '').title(),
                                                                         "description": "", "type": "form",
                                                                         "id": last_id + 1, "action": "init"}}
                if f"root/{name.replace('.yml.meta', '')}" not in wizard_data:
                    file.write("\n")
                    yaml.dump(wizard_form, file)
    file.close()
