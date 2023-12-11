import copy
import logging
import subprocess

from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from hydra_engine.schemas import set_value, HydraParametersInfo, ParameterSaveInfo,filter_tree,find_form
from hydra_engine.search.searcher import HydraSearcher

logger = logging.getLogger("common_logger")
router = APIRouter(prefix="/hydra", tags=["hydra"])
templates = Jinja2Templates(directory="hydra_engine/static")


@router.get("/tree")
def get_forms():
    try:
        forms = filter_tree(copy.deepcopy(HydraParametersInfo().get_tree_structure()))
        return JSONResponse(content=jsonable_encoder(forms), status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"detail": "File or directory not found"}, status_code=400)


@router.get("/tree/{name:path}")
def get_form_info(name: str):
    form = find_form(name.split("/"), copy.deepcopy(HydraParametersInfo().get_tree_structure()))
    return JSONResponse(content=jsonable_encoder(form), status_code=200)


@router.post("/elements/values")
async def set_values(content: list[ParameterSaveInfo]):
    for item in content:
        set_value(item.input_url, item.file_id, item.value)


@router.post("/configuration")
def reset():
    cmd = "git config --global --add safe.directory /code/files && git reset --hard HEAD"
    result = subprocess.run(cmd, shell=True, check=True, cwd="/code/files")
    if result.returncode == 0:
        return {"reset": "successful"}
    logger.error(f"Error when try to reset configuration to last stable condition with {result.stderr}")
    return JSONResponse(content={"reset": "error when reset configuration"}, status_code=500)


@router.post("/debug_s1")
def debug1():
    return HydraParametersInfo().get_tree_structure()


@router.get("/search")
async def search(q,
                 pagenum: int = Query(title='page number of search results',
                                      ge=1, default=None),
                 pagelen: int = Query(title='count of page results in single page to return',
                                      ge=1, le=None, default=None)
                 ):
    results = await HydraSearcher().perform_search(q, pagenum, pagelen)
    return JSONResponse(content=results) if results != 'not exists' else JSONResponse(content={'index': results})

