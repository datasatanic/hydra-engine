import logging
import os
from contextlib import asynccontextmanager

import ruamel.yaml
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette_prometheus import metrics, PrometheusMiddleware


from hydra_engine import router, wizard_router
from hydra_engine.configs import config
from hydra_engine.parser import parse_config_files
from hydra_engine.schemas import HydraParametersInfo, read_wizard_file,read_ui_file,generate_wizard_meta
from hydra_engine.search.index_schema import HydraIndexScheme
from hydra_engine.search.searcher import HydraSearcher

yaml = ruamel.yaml.YAML(typ="rt")
logger = logging.getLogger("common_logger")
base_dir = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def startup_event(app: FastAPI):
    logger.debug("Start parsing directory")
    parse_config_files()
    read_ui_file(config.filespath)
    generate_wizard_meta(config.filespath)
    read_wizard_file(config.filespath)
    HydraParametersInfo().set_modify_time()
    logger.debug("Directory has been parsed successfully")
    await HydraSearcher(index_name="HYDRA", schema=HydraIndexScheme()).reindex_hydra()
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


#app_static.mount("/", StaticFiles(directory=os.path.join(base_dir, "wwwroot"), html=True), "client")
