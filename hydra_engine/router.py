import copy
import logging
import os
import subprocess

from fastapi import APIRouter, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, FileResponse

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


@router.post("/elements/values", response_class=FileResponse)
def set_values(content: list):
    for item in content:
        set_value(item["Value"]["Key"], item["Key"], item["Value"]["Value"])
    cmd = "terragrunt run-all plan -json > test.json"
    cmd2 = "terragrunt graph -type=plan | dot -Tsvg > graph.svg"
    subprocess.Popen(cmd, shell=True)
    subprocess.Popen(cmd2, shell=True, cwd="/code/files")
    for root, dirs, files in os.walk("files"):
        for name in files:
            if name == "graph.svg":
                return os.path.join(root, name)


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
