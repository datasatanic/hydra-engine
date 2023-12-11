import copy
import logging

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from hydra_engine.schemas import HydraParametersInfo, find_form

logger = logging.getLogger("common_logger")
router = APIRouter(prefix="/wizard", tags=["wizard"])


@router.get("/tree")
def get_wizard_tree():
    try:
        return JSONResponse(content=jsonable_encoder(copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure())),
                            status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"detail": "File or directory not found"}, status_code=400)


@router.get("/tree/{name:path}")
def get_wizard_form(name: str):
    form = find_form(name.split("/"), copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure()))
    return JSONResponse(content=jsonable_encoder(form), status_code=200)
