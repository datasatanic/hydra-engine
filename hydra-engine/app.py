from schemas import add_node, tree, add_additional_fields
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()


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


@app.get("/tree")
def get_tree(file_name: str):
    try:
        read_file(file_name)
        return JSONResponse(content=jsonable_encoder(tree), status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"detail": "File or directory not found"}, status_code=400)
