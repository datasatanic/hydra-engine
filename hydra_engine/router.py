import copy
import logging
import os
import subprocess

from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse, PlainTextResponse

from hydra_engine.schemas import tree, get_element_info, set_value, get_value
from hydra_engine.search.searcher import HydraSearcher

logger = logging.getLogger("common_logger")
router = APIRouter(prefix="/hydra")


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


@router.post("/elements/values", response_class=PlainTextResponse)
def set_values(content: list):
    for item in content:
        set_value(item["Value"]["Key"], item["Key"], item["Value"]["Value"])
    cmd = "terragrunt plan -out=test.out"
    cmd2 = "terragrunt show -json test.out > test.json"
    proc = subprocess.run(cmd, shell=True, cwd="/code/files")
    # proc.wait(timeout=30)
    proc2 = subprocess.run(cmd2, shell=True, cwd="/code/files")
    cmd3 = "terraform-visual --plan test.json"
    subprocess.run(cmd3, shell=True, cwd="/code/files")
    # proc2.wait(timeout=30)
    return "plan/index.html"


@router.get("/plan/apply")
def apply_plan():
    cmd = "terragrunt run-all apply --terragrunt-non-interactive"
    proc = subprocess.Popen(cmd, shell=True)
    return {"plan": "apply"}


@router.get("/reset/configuration")
def reset():
    cmd = "git reset --hard HEAD"
    subprocess.Popen(cmd, shell=True, cwd="/code/files")
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
