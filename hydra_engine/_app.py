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
from hydra_engine.schemas import add_node, HydraParametersInfo, add_additional_fields
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


app_static.mount("/", StaticFiles(directory="wwwroot", html=True), "client")


def read_controls_file(directory):
    """
        Reads meta file of tree and creates structured tree
    """
    input_url_pattern = r'^[a-zA-Z0-9_/\\.-]+:$'
    display_name_pattern = r"\s*display_name:\s*[\"'].*[\"']"
    description_pattern = r"\s*description:\s*[\"'].*[\"']"
    type_pattern = r"\s*type:\s*[\"'].*[\"']"
    HydraParametersInfo().tree.clear()
    path = ""
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == "ui.meta" and "terragrunt-cache" not in root:
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
                                type_match = re.match(type_pattern, line)
                                if description_match or display_name_match or type_match:
                                    add_additional_fields(path.split("/"), str_list)
                                else:
                                    raise ValueError(f"Not valid line {line.strip()}")
                    break
                except Exception as e:
                    logger.error(f"Error in parsing 'ui.meta' {e}")
                    return
