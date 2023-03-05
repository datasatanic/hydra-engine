import copy
import logging
import os
from fastapi import FastAPI, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from hydra_engine.schemas import add_node, tree, add_additional_fields, get_element_info, set_value, get_value
from hydra_engine.parser import parse_config_files
from hydra_engine.search.searcher import HydraSearcher
from hydra_engine.search.index_schema import HydraIndexScheme

from starlette_prometheus import metrics, PrometheusMiddleware

logger = logging.getLogger("common_logger")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(PrometheusMiddleware)

app.get("/metrics", name='metrics')(metrics)


def read_controls_file(directory):
    """
        Reads meta file of tree and creates structured tree
    """
    tree.clear()
    path = ""
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == "controls.meta":
                try:
                    f = open(os.path.join(root, name))
                    for line in f:
                        str_list = list(filter(lambda x: len(x), line.replace('\n', '').strip().split(":")))
                        if line != '\n':
                            if len(str_list) == 1:
                                path = str_list[0]
                                add_node(path.split("/"))
                            else:
                                add_additional_fields(path.split("/"), str_list)
                except Exception as e:
                    logger.error(f"Error in parsing meta file of tree {e}")


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


@app.on_event("startup")
async def startup_event():
    logger.debug("Start parsing directory")
    try:
        parse_config_files()
        read_controls_file("files")
        logger.debug("Directory has been parsed successfully")
    except Exception as e:
        logger.error(f"Error in parsing files with {e}")
    await HydraSearcher(index_name="HYDRA", schema=HydraIndexScheme()).reindex_hydra()


@app.get('/health')
async def stats():
    return {'service': 'hydra-engine', 'status': 'Serve'}


@app.get("/tree")
def get_forms():
    try:
        forms = filter_tree(copy.deepcopy(tree))
        return JSONResponse(content=jsonable_encoder(forms), status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"detail": "File or directory not found"}, status_code=400)


@app.get("/tree/{name:path}")
def get_form_info(name: str):
    groups = find_groups(name.split("/"), copy.deepcopy(tree))
    return JSONResponse(content=jsonable_encoder(groups), status_code=200)


@app.get("/elements/info/{input_url:path}")
def get_element(input_url: str, file_path):
    return JSONResponse(get_element_info(input_url, file_path).__dict__)


@app.get("/element/value/{file_id}/{input_url:path}")
def get_element_value(input_url: str, file_id: str):
    return get_value(input_url, file_id)


@app.post("/elements/values")
def set_values(content: list):
    for item in content:
        set_value(item["Value"]["Key"], item["Key"], item["Value"]["Value"])
    return content


@app.get("/update/data")
def update_data():
    parse_config_files()
    read_controls_file("files/controls.meta")
    return {"message": "ok"}


@app.post("/debug_s1")
def debug1():
    return tree


@app.get("/search")
async def search(q,
                 pagenum: int = Query(title='page number of search results',
                                      ge=1, default=None),
                 pagelen: int = Query(title='count of page results in single page to return',
                                      ge=1, le=None, default=None)
                 ):
    results = await HydraSearcher().perform_search(q, pagenum, pagelen)
    return JSONResponse(content=results) if results != 'not exists' else JSONResponse(content={'index': results})
