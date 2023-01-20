import copy
from schemas import add_node, tree, add_additional_fields, get_element_info, set_value, get_value
from parser import parse_config_files
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = [
    "http://localhost",
    "http://localhost:8080",
    "https://localhost:7285"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def read_controls_file(file_name: str):
    tree.clear()
    path = ""
    f = open(file_name)
    for line in f:
        str_list = list(filter(lambda x: len(x), line.replace('\n', '').strip().split(":")))
        if line != '\n':
            if len(str_list) == 1:
                path = str_list[0]
                add_node(path.split("/"))
            else:
                add_additional_fields(path.split("/"), str_list)


def filter_tree(all_tree):
    tree_filter = all_tree
    keys = list(tree_filter)
    for key in keys:
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
    parse_config_files()
    read_controls_file("files/controls.meta")


@app.get("/tree")
def get_forms():
    try:
        forms = filter_tree(copy.deepcopy(tree))
        return JSONResponse(content=jsonable_encoder(forms), status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"detail": "File or directory not found"}, status_code=400)


@app.get("/tree/{name:path}")
def get_groups(name: str):
    groups = find_groups(name.split("/"), copy.deepcopy(tree))
    return JSONResponse(content=jsonable_encoder(groups), status_code=200)


@app.get("/elements/info/{input_url:path}")
def get_element(input_url: str, file_path):
    return JSONResponse(get_element_info(input_url, file_path).__dict__)


@app.get("/element/value/{file_id}/{input_url:path}")
def get_element_value(input_url: str, file_id: str):
    return get_value(input_url, file_id)


@app.post("/elements/values/{file_id:str}")
def set_values(file_id: str, content: dict):
    set_value(content["Key"], file_id, content["Value"])


@app.get("/update/data")
def update_data():
    parse_config_files()
    read_controls_file("files/controls.meta")
    return {"message": "ok"}
