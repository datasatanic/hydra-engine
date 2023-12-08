import logging
import os
import ruamel.yaml
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

yaml = ruamel.yaml.YAML(typ="rt")
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
    parse_config_files()
    read_controls_file(os.path.join(base_dir, "files"))
    logger.debug("Directory has been parsed successfully")
    await HydraSearcher(index_name="HYDRA", schema=HydraIndexScheme()).reindex_hydra()


app_static.mount("/", StaticFiles(directory=os.path.join(base_dir, "wwwroot"), html=True), "client")


def read_controls_file(directory):
    """
        Reads meta file of tree and creates structured tree
    """
    HydraParametersInfo().tree.clear()
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == "ui.meta":
                with open(os.path.join(root, name), 'r') as stream:
                    data_loaded = yaml.load(stream)
                    for obj in data_loaded:
                        path = obj.split("/")
                        add_node(path, int(data_loaded[obj]["id"]), data_loaded[obj]["type"])
                        add_additional_fields(path, "display_name", data_loaded[obj]["display_name"])
                        if "description" in data_loaded[obj]:
                            add_additional_fields(path, "description", data_loaded[obj]["description"])
