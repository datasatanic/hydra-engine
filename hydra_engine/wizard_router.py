import copy
import logging

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from hydra_engine.schemas import HydraParametersInfo, find_form, Condition

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
    if name is None or name == "":
        root = copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure())
        [root[key].child.clear() for key in root]
        [root[key].elem.clear() for key in root]
        return JSONResponse(content=jsonable_encoder(root),
                            status_code=200)
    form = find_form(name.split("/"), copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure()), is_wizard=True)
    return JSONResponse(content=jsonable_encoder(form), status_code=200)


@router.post("/form/condition")
def check_condition(path, condition: list[Condition]):
    form = find_form(path.split("/"), copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure()))
    form_condition = form[path.split("/")[-1]].condition
    if form_condition == condition:
        return JSONResponse(content={"equals": True}, status_code=200)
    return JSONResponse(content={"info": "Not valid form condition"}, status_code=400)
