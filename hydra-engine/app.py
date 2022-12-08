from schemas import add_node, tree
from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI

app = FastAPI()


def read_file():
    tree.clear()
    f = open('controls.meta')
    for line in f:
        str_list = list(filter(lambda x: len(x), line.replace('\n', '').split(":")))
        if len(str_list) == 1 and line != '\n':
            print(line.replace('\n', "").split(":"))
            add_node(str_list[0].split("/"))


@app.get("/")
def get_tree():
    read_file()
    print_tree(tree)
    return {"tree": jsonable_encoder(tree)}


def print_tree(dir_tree):
    for item in dir_tree:
        print("---" * item.level, item.name)
        if len(item.child_items) > 0:
            print_tree(item.child_items)
