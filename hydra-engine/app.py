import copy

from schemas import add_node, tree, add_additional_fields, Group
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


def read_file(file_name: str):
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


def find_groups(name, all_tree):
    if name in all_tree:
        keys = list(all_tree[name].child)
        for key in keys:
            if len(all_tree[name].child[key].child) > 0:
                all_tree[name].child[key].type = "form"
                all_tree[name].child[key].child.clear()
            else:
                all_tree[name].child[key].type = "group"
        return all_tree[name]
    for value in all_tree.values():
        return find_groups(name, value.child)


@app.get("/tree")
def get_forms():
    try:
        read_file("controls.meta")
        forms = filter_tree(copy.deepcopy(tree))
        return JSONResponse(content=jsonable_encoder(forms), status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"detail": "File or directory not found"}, status_code=400)


@app.get("/tree/{name}")
def get_groups(name: str):
    groups = find_groups(name, copy.deepcopy(tree))
    return JSONResponse(content=jsonable_encoder(groups), status_code=200)
