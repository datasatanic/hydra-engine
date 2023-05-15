import copy
import logging
import json
import subprocess
import os
import uuid

from fastapi import APIRouter, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from hydra_engine.schemas import tree, get_element_info, set_value, get_value
from hydra_engine.search.searcher import HydraSearcher

logger = logging.getLogger("common_logger")
router = APIRouter(prefix="/hydra")
templates = Jinja2Templates(directory="hydra_engine/static")


@router.get("/tree")
def get_forms():
    try:
        forms = filter_tree(copy.deepcopy(tree))
        return JSONResponse(content=jsonable_encoder(forms), status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"detail": "File or directory not found"}, status_code=400)


@router.get("/tree/{name:path}")
def get_form_info(name: str):
    groups = find_groups(name.split("/"), copy.deepcopy(tree))
    return JSONResponse(content=jsonable_encoder(groups), status_code=200)


@router.get("/elements/info/{input_url:path}")
def get_element(input_url: str, file_path):
    return JSONResponse(get_element_info(input_url, file_path).__dict__)


@router.get("/element/value/{file_id}/{input_url:path}")
def get_element_value(input_url: str, file_id: str):
    return get_value(input_url, file_id)


@router.post("/elements/values", response_class=HTMLResponse)
async def set_values(request: Request, content: list):
    for item in content:
        set_value(item["Value"]["Key"], item["Key"], item["Value"]["Value"])
    result = run_terragrunt_plan()
    if result.returncode == 0:
        logger.info("Plan generated successfully")
        for root, dirs, files in os.walk("files"):
            for name in files:
                if name == "test.json" and "terragrunt-cache" not in root:
                    with open(os.path.join(root, name)) as file:
                        plan = json.load(file)
        return templates.TemplateResponse("plan.html",
                                          {"request": request, "plan": {"plan": find_changes_in_terraform_plan(plan)},
                                           "id": uuid})
    else:
        logger.error(f"Error when form plan with {result.stderr}")


def run_terragrunt_plan():
    cmd = "terragrunt plan -out=test.out && terragrunt show -json test.out > test.json"
    result = subprocess.run(cmd, shell=True, cwd="/code/files", check=True, stdout=subprocess.DEVNULL)
    return result


@router.get("/plan/apply")
def apply_plan():
    cmd = "terragrunt run-all apply --terragrunt-non-interactive"
    result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL)
    if result.returncode == 0:
        logger.info("Plan apply completed")
        return {"plan": "apply"}
    else:
        logger.error(f"Error when plan applied with {result.stderr}")
        return JSONResponse(content={"plan": "not apply"}, status_code=500)


@router.get("/reset/configuration")
def reset():
    cmd = "git reset --hard HEAD"
    cmd2 = "git config --global --add safe.directory /code/files && git branch"
    subprocess.run(cmd2, shell=True, cwd="/code/files")
    return {"reset": "successful"}


@router.post("/debug_s1")
def debug1():
    return tree


@router.get("/search")
async def search(q,
                 pagenum: int = Query(title='page number of search results',
                                      ge=1, default=None),
                 pagelen: int = Query(title='count of page results in single page to return',
                                      ge=1, le=None, default=None)
                 ):
    results = await HydraSearcher().perform_search(q, pagenum, pagelen)
    return JSONResponse(content=results) if results != 'not exists' else JSONResponse(content={'index': results})


def filter_tree(all_tree):
    """
        Deletes empty nodes with no child elements
    """
    tree_filter = all_tree
    keys = list(tree_filter)
    for key in keys:
        tree_filter[key].elem.clear()
        if len(tree_filter[key].child) == 0:
            tree_filter.pop(key)
        else:
            filter_tree(tree_filter[key].child)
    return tree_filter


def find_groups(path, all_tree):
    name = path[0]
    if name in all_tree:
        keys = list(all_tree[name].child)
        for key in keys:
            if len(all_tree[name].child[key].child) > 0:
                all_tree[name].child[key].type = "form"
                if len(path) == 1:
                    all_tree[name].child[key].child.clear()
            else:
                all_tree[name].child[key].type = "group"
        if len(path) > 1:
            path.remove(name)
            return find_groups(path, all_tree[name].child)
        else:
            return {name: all_tree[name]}


def find_changes_in_terraform_plan(plan_dict):
    resource_changes = plan_dict["resource_changes"]
    changes_dict = {}
    for resource in resource_changes:
        resource_address = resource["address"]
        changes_dict[resource_address] = {"old": {}, "new": {}}
        change_after = resource.get("change").get("after")
        change_after_unknown = resource.get("change").get("after_unknown")
        change_before = resource.get("change").get("before")
        change_actions = resource.get("change").get("actions")
        if "no-op" not in change_actions:
            for key, value in change_before.items():
                new_value = None
                old_value = value
                if key in change_after:
                    new_value = change_after.get(key)
                if key not in change_after and key in change_after_unknown:
                    changes_dict[resource_address]["old"][key] = old_value
                    changes_dict[resource_address]["new"][key] = "known after apply"
                elif old_value != new_value and (
                        new_value is not None and new_value != "" or old_value is not None and old_value != ""):
                    changes_dict[resource_address]["old"][key] = old_value
                    changes_dict[resource_address]["new"][key] = new_value
            for key, value in change_after.items():
                if key not in change_before:
                    new_value = value
                    changes_dict[resource_address]["new"][key] = new_value
        else:
            for key, value in change_before.items():
                changes_dict[resource_address]["old"][key] = value
        resource[resource_address] = {"actions": change_actions, "values_change": changes_dict[resource_address]}
        resource.pop("change")
        resource.pop("address")
        for key in list(resource):
            if key != resource_address:
                resource[resource_address][key] = resource[key]
                resource.pop(key)
    return plan_dict
