from schemas import add_node, tree, add_additional_fields
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


@app.get("/tree")
def get_tree(file_name: str):
    try:
        read_file(file_name)
        forms = filter_tree(tree)
        return JSONResponse(content=jsonable_encoder(forms), status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"detail": "File or directory not found"}, status_code=400)
