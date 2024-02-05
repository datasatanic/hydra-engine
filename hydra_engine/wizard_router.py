import asyncio
import copy
import logging
import subprocess
import sys
import time
from configs import config
from typing import Optional
from fastapi import APIRouter
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.encoders import jsonable_encoder
import hydra_engine.filewatcher
from hydra_engine.schemas import HydraParametersInfo, find_form, Condition, update_wizard_meta, ParameterSaveInfo, \
    set_value, check_validate_parameter

logger = logging.getLogger("common_logger")
router = APIRouter(prefix="/wizard", tags=["wizard"])


class DeployProcess:
    def __init__(self):
        self.deploy_process: Optional[subprocess.Popen] = None
        self.site_name: str = ""


deploy_site = DeployProcess()


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
            check = check_validate_parameter(item.input_url, item.value, item.file_id,
                                             wizard_form[next(iter(wizard_form.keys()))])
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
async def init_arch(name: str):
    try:
        command = f"GIT_SERVER_ADDRESS=10.74.106.14:/srv/git CCFA_VERSION=0.1.0-pc ENVIRONMENT_DIR=. ./_framework/scripts/env/init.sh {name}"
        init_process = subprocess.run(command, cwd=config.filespath, shell=True, check=True)
        if init_process.returncode == 0:
            logger.info(f"init arch with name: {name}")
            update_wizard_meta(config.filespath, name)
            if HydraParametersInfo().was_modified:
                hydra_engine.filewatcher.file_event.wait(timeout=60)
                HydraParametersInfo().was_modified = False
            return JSONResponse(content={"message": "OK"}, status_code=200)
        else:
            return JSONResponse(content={"message": "Bad request"}, status_code=400)
    except Exception as e:
        print(e)
        return JSONResponse(content={"message": "Bad request"}, status_code=400)


@router.post("/deploy")
def deploy_site(name: str):
    try:
        logger.info(f"deploy site with name: {name}")
        command = f'python -c "from hydra_engine.wizard_router import use_deploy_script; use_deploy_script(\'{name}\')"'
        deploy_site.deploy_process = subprocess.Popen(command, shell=True)
        deploy_site.site_name = name
        return JSONResponse(content={"message": f"Starting deploy {name}"}, status_code=200)
    except Exception as e:
        logger.error(e)
        return JSONResponse(content={"message": str(e)}, status_code=400)


@router.get("/check-deploy")
def check_deploy():
    if deploy_site.deploy_process is None:
        return PlainTextResponse("stop")
    elif deploy_site.deploy_process.poll() is None:
        return PlainTextResponse("completing")
    elif deploy_site.deploy_process.poll() is not None:
        if deploy_site.deploy_process.returncode == 0:
            deploy_site.deploy_process = None
            return PlainTextResponse("completed")
        else:
            deploy_site.deploy_process = None
            return PlainTextResponse("failed")


def use_deploy_script(site_name):
    time.sleep(10)
    print(f"Deploy ending for {site_name}")
    sys.exit(1)
