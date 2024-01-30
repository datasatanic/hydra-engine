import copy
import json
import logging
from typing import Dict, List

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

import hydra_engine.filewatcher
from hydra_engine.schemas import HydraParametersInfo, find_form, Condition, update_wizard_meta, ParameterSaveInfo, \
    set_value, check_validate_parameter

logger = logging.getLogger("common_logger")
router = APIRouter(prefix="/wizard", tags=["wizard"])


@router.post("/tree/{name:path}")
def get_wizard_form(name: str, conditions: list[Condition]):
    if name is None or name == "":
        root = copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure())
        [root[key].child.clear() for key in root]
        [root[key].elem.clear() for key in root]
        return JSONResponse(content=jsonable_encoder(root),
                            status_code=200)
    form = find_form(name.split("/"), copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure()), is_wizard=True)
    if form:
        form_condition = form[name.split("/")[-1]].condition
        if form_condition == conditions:
            return JSONResponse(content=jsonable_encoder(form), status_code=200)
        else:
            return JSONResponse(content={"message": "Not valid conditions to show form"}, status_code=400)
    else:
        return JSONResponse(content={"message": "Form not found"}, status_code=404)


@router.post("/elements/values")
async def set_values(name: str, content: list[ParameterSaveInfo]):
    try:
        wizard_form = find_form(name.split("/"), copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure()), True)
        if wizard_form is None:
            return JSONResponse(content={"message": "Form not found"}, status_code=404)
        for item in content:
            check = check_validate_parameter(item.input_url, item.value, item.file_id, wizard_form[next(iter(wizard_form.keys()))])
            if check is not True:
                return JSONResponse(content={"message": check}, status_code=400)
            set_value(item.input_url, item.file_id, item.value)
        if HydraParametersInfo().was_modified:
            hydra_engine.filewatcher.file_event.wait()
            HydraParametersInfo().was_modified = False
        return JSONResponse(content=jsonable_encoder(HydraParametersInfo().modify_time), status_code=200)
    except ValueError:
        return JSONResponse(content={"message": "Bad request"}, status_code=400)


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
