import copy
import logging
import subprocess
import time
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from hydra_engine.configs import config
from hydra_engine.parser import parse_config_files
from hydra_engine.schemas import find_form, Condition, update_wizard_meta, ParameterSaveInfo, \
    set_value, check_validate_parameter, WizardInfo, HydraParametersInfo, WizardState, Arch, Site, read_ui_file, \
    read_wizard_file, set_comment_out,CommentItem

logger = logging.getLogger("common_logger")
router = APIRouter(prefix="/wizard", tags=["wizard"])

deploy_process = None


@router.get("/tree")
def get_wizard_tree():
    try:
        forms = HydraParametersInfo().get_wizard_tree_structure()
        return JSONResponse(content=jsonable_encoder(forms), status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"detail": "File or directory not found"}, status_code=400)


@router.get("/wizard-state")
def get_current_step():
    if WizardInfo().wizard_state is None:
        WizardInfo().wizard_state = WizardState(current_step="", arch=Arch(arch_name="", status="not completed"),
                                                sites=[])
    return JSONResponse(content=jsonable_encoder(WizardInfo().wizard_state), status_code=200)


@router.post("/tree/{name:path}")
def get_wizard_form(name: str, conditions: list[Condition]):
    if name is None or name == "":
        root = copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure())
        [root[key].child.clear() for key in root]
        [root[key].elem.clear() for key in root]
        WizardInfo().update_current_step("root")
        return JSONResponse(content=jsonable_encoder(root),
                            status_code=200)
    form = find_form(name.split("/"), copy.deepcopy(HydraParametersInfo().get_wizard_tree_structure()), is_wizard=True)
    if form:
        form_condition = form[name.split("/")[-1]].condition
        if form_condition == conditions:
            WizardInfo().update_current_step(name)
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
            check, item.value = check_validate_parameter(item.input_url, item.value, item.file_id,
                                                         wizard_form[next(iter(wizard_form.keys()))])
            if check is False:
                return JSONResponse(content={"message": check}, status_code=400)
            set_value(item.input_url, item.file_id, item.value)
        read_wizard_file(config.filespath)
        return JSONResponse(content=jsonable_encoder(HydraParametersInfo().modify_time), status_code=200)
    except ValueError:
        return JSONResponse(content={"message": "Bad request"}, status_code=400)


@router.post("/init_arch")
async def init_arch(name: str):
    WizardInfo().update_arch_status("in progress")
    command = f"GIT_SERVER_ADDRESS=10.74.106.14:/srv/git CCFA_VERSION=0.1.0-pc ENVIRONMENT_DIR=. ./_framework/scripts/env/init.sh {name}"
    init_process = subprocess.run(command, cwd=config.filespath, shell=True, check=True)
    if init_process.returncode == 0:
        update_wizard_meta(config.filespath, name)
        parse_config_files()
        read_ui_file(config.filespath)
        read_wizard_file(config.filespath)
        logger.info(f"init arch with name: {name}")
        WizardInfo().update_arch_name(name)
        WizardInfo().update_arch_status("completed")
        return JSONResponse(content={"message": "OK"}, status_code=200)
    else:
        WizardInfo().update_arch_status("not completed")
        WizardInfo().update_arch_name("")
        return JSONResponse(content={"message": "Bad request"}, status_code=400)


@router.post("/deploy")
def deploy_site(name: str, step_number: int):
    global deploy_process
    try:
        logger.info(f"deploy site with name: {name}")
        command = f"ENVIRONMENT_DIR=. ./_framework/scripts/env/deploy.sh {WizardInfo().get_current_arch_name()} {name} 10"
        deploy_process = subprocess.Popen(command, cwd=config.filespath, shell=True)
        site = Site(site_name=name, status="in progress", step_number=step_number)
        for exist_site in WizardInfo().get_sites_info():
            if site.site_name == exist_site.site_name:
                WizardInfo().remove_site(exist_site)
                break
        WizardInfo().add_site(site)
        return JSONResponse(content=jsonable_encoder(WizardInfo().get_sites_info()), status_code=200)
    except Exception as e:
        logger.error(e)
        return JSONResponse(content={"message": str(e)}, status_code=400)


@router.get("/check-deploy")
def check_deploy():
    global deploy_process
    if deploy_process is None:
        WizardInfo().get_sites_info()[-1].status = "not completed"
        return JSONResponse(jsonable_encoder(WizardInfo().get_sites_info()), status_code=200)
    elif deploy_process.poll() is None:
        WizardInfo().get_sites_info()[-1].status = "in progress"
        return JSONResponse(jsonable_encoder(WizardInfo().get_sites_info()), status_code=200)
    elif deploy_process.poll() is not None:
        if deploy_process.returncode == 0:
            deploy_process = None
            WizardInfo().get_sites_info()[-1].status = "completed"
            return JSONResponse(jsonable_encoder(WizardInfo().get_sites_info()), status_code=200)
        else:
            deploy_process = None
            WizardInfo().get_sites_info()[-1].status = "failed"
            return JSONResponse(jsonable_encoder(WizardInfo().get_sites_info()), status_code=200)


@router.post("/comment-out")
def comment_out(content: list[CommentItem]):
    set_comment_out(content)
    parse_config_files()
    read_wizard_file(config.filespath)

def use_deploy_script(site_name):
    time.sleep(10)
    print(f"Deploy ending for {site_name}")
