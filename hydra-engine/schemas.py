import copy
import datetime
from typing import List
import json
import yaml
from pydantic import BaseModel, validator, Extra, parse_obj_as
from parser import elements_yaml, elements_files_info, write_file, elements_json
import uuid
import os

tree = {}


class ElemInfo(BaseModel):
    value: object
    type: str
    description: str = None
    sub_type: str = None
    readOnly: bool = False
    display_name: str
    control: str
    constraints: List = []

    @validator("type")
    def check_type(cls, value_type, values, **kwargs):
        if value_type == "string":
            return True
        elif value_type == "int":
            try:
                int(values["value"])
                return value_type
            except TypeError:
                return ValueError("Not integer type")
        elif value_type == "bool":
            if values["value"] == "True" or values["value"] == "False":
                return value_type
            return ValueError("Not boolean type")
        elif value_type == "double":
            try:
                float(values["value"])
                return value_type
            except TypeError:
                return ValueError("Not double type")
        elif value_type == "datetime":
            try:
                datetime.datetime.strptime(values["value"], '%b %d %Y %I:%M%p')
                return value_type
            except TypeError:
                return ValueError("Not datetime type")
        elif value_type == "array":
            return value_type


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
                    elem_list.append({key: file_path})
    return elem_list


def get_value(input_url: str, file_path: str):
    input_url_list = input_url.split("/")
    key = input_url_list[0]
    for elements in elements_json:
        if key in elements.values and elements.path == file_path:
            return find_value_in_dict(elements.values, input_url_list)


def find_value_in_dict(elements, input_url_list):
    while len(input_url_list) > 0:
        elements = elements[input_url_list[0]]
        input_url_list.pop(0)
    return elements


def set_value_in_dict(elements, value, input_url_list):
    while len(input_url_list) > 1:
        elements = elements[input_url_list[0]]
        input_url_list.pop(0)
    elements[input_url_list[0]] = value


def set_value(input_url: str, file_path: str, value: str):
    input_url_list = input_url.split("/")
    key = input_url_list[0]
    for elements in elements_json:
        if key in elements.values and elements.path == file_path:
            set_value_in_dict(elements.values, value, input_url_list)
            return write_file(elements.values, file_path)


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
                                     constraints=render_dict["constraints"], value=get_value(input_url, file_path))
                return elem_info
