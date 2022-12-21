from typing import List
import json
import yaml
from pydantic import BaseModel, validator, Extra, parse_obj_as
from parser import elements_yaml, elements_json,elements_files_info
import os

tree = {}


class ElemInfo(BaseModel):
    type: str
    description: str = None
    sub_type: str = None
    readOnly: bool = False
    display_name: str
    control: str
    constraints: List = []


class Node(BaseModel):
    child: dict = {}
    elem: List = []

    class Config:
        extra = Extra.allow


def add_node(_list):
    level = len(_list)
    if level == 1:
        node = Node(elem=[], child={})
        node.elem = get_elements("/".join(_list))
        d = {_list[0]: node}
        tree.update(d)
    else:
        add_node_subtree(tree, 0, _list)


def add_node_subtree(subtree, j, _list):
    n = len(subtree)
    for i in range(0, n):
        if _list[j] in subtree:
            subtree = subtree[_list[j]].child
            j += 1
            if j == len(_list) - 1:
                node = Node(elem=[], child={})
                node.elem = get_elements("/".join(_list))
                d = {_list[j]: node}
                subtree.update(d)
                return
            add_node_subtree(subtree, j, _list)


def add_additional_fields(node_list, field_list):
    node = find_node(node_list)
    if field_list[0] in node.__dict__:
        raise ValueError("Not valid file")
    node.__dict__[field_list[0]] = field_list[1].replace('"', '').strip()


def find_node(node_list):
    subtree = tree
    find = {}
    for node in node_list:
        find = subtree[node] if node in subtree else find
        subtree = find.child
    return find


def get_elements(output_url):
    elem_list = []
    for elements in elements_yaml:
        for item in elements:
            keys = list(item)
            for key in keys:
                if item[key]["output_url"] == output_url:
                    file_path = elements_files_info[elements_yaml.index(elements)]["path"]
                    elem_list.append({key: get_value(key, file_path), "path": file_path})
    return elem_list


def get_value(input_url: str, file_path: str):
    input_url_list = input_url.split("/")
    d = {}
    for key in input_url_list:
        for elements in elements_json:
            d = elements[key] if key in elements and elements["path"] == file_path else d
        return d[input_url_list[-1]]


def get_element_info(input_url, file_path: str):
    for elements in elements_yaml:
        for item in elements:
            if input_url in item and elements_files_info[elements_yaml.index(elements)]["path"] == file_path:
                element = item[input_url]
                if len(element) == 0:
                    return None
                render_dict = element["render"]
                elem_info = ElemInfo(type=element["type"], description=element["description"],
                                     sub_type=element["sub_type"],
                                     readOnly=element["readonly"],
                                     display_name=render_dict["display_name"], control=render_dict["??? control"],
                                     constraints=render_dict["constraints"])
                return elem_info
