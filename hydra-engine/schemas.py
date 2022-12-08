from typing import List
import json
from pydantic import BaseModel

tree_dict = {}
tree = []


class Node(BaseModel):
    name: str
    level: int
    child_items: List | None = None


def add_node(_list):
    level = len(_list)
    if level == 1:
        node = Node(name=_list[0], child_items=[], level=1)
        tree.append(node)
    else:
        add_node_subtree(tree, 0, _list)


def add_node_subtree(subtree, j, _list):
    n = len(subtree)
    for i in range(0, n):
        if subtree[i].name == _list[j]:
            j += 1
            subtree = subtree[i].child_items
            if j == len(_list) - 1:
                node = Node(name=_list[j], child_items=[], level=j + 1)
                subtree.append(node)
                return
            add_node_subtree(subtree, j, _list)
