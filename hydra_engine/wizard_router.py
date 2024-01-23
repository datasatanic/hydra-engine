import copy
import logging
from typing import Dict

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

import hydra_engine.filewatcher
from hydra_engine.schemas import HydraParametersInfo, find_form, Condition, update_wizard_meta

logger = logging.getLogger("common_logger")
router = APIRouter(prefix="/wizard", tags=["wizard"])


@router.get("/tree")
def get_wizard_tree():
    try:
        return JSONResponse(content=jsonable_encoder(copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure())),
                            status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"detail": "File or directory not found"}, status_code=400)


@router.post("/tree/{name:path}")
def get_wizard_form(name: str, conditions: list[Condition], prev_form_values: list = None):
    if name is None or name == "":
        root = copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure())
        [root[key].child.clear() for key in root]
        [root[key].elem.clear() for key in root]
        return JSONResponse(content=jsonable_encoder(root),
                            status_code=200)
    form = find_form(name.split("/"), copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure()), is_wizard=True)
    if form:
        form_condition = form[name.split("/")[-1]].condition
        flag = True
        if prev_form_values:
            for item in prev_form_values:
                if not check_exist_values(item):
                    flag = False
                    break
        if form_condition == conditions and flag:
            return JSONResponse(content=jsonable_encoder(form), status_code=200)
        else:
            return JSONResponse(content={"message": "Not valid conditions to show form"}, status_code=400)
    else:
        return JSONResponse(content={"message": "Form not found"}, status_code=404)




@router.post("/init_arch")
def init_arch(name: str):
    try:
        logger.info(f"init arch with name: {name}")
        update_wizard_meta("files", name)
        if HydraParametersInfo().was_modified:
            hydra_engine.filewatcher.file_event.wait()
            HydraParametersInfo().was_modified = False
        return JSONResponse(content={"message": "OK"}, status_code=200)
    except Exception as e:
        logger.error(e)
        return JSONResponse(content={"message": "Bad request"}, status_code=400)


@router.post("/deploy")
def deploy_site(name: str):
    try:
        logger.info(f"deploy site with name: {name}")
        return JSONResponse(content={"message": "OK"}, status_code=200)
    except Exception as e:
        logger.error(e)
        return JSONResponse(content={"message": e}, status_code=400)


def check_exist_values(parameter_value):
    print(parameter_value)
    for key, value in parameter_value:
        if isinstance(value, dict):
            if not check_exist_values(value):
                return False
        elif isinstance(value, list):
            for item in value:
                if not check_exist_values(item):
                    return False
        else:
            if value is None or value == "":
                return False
