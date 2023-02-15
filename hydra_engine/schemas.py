from datetime import datetime
import maya
from typing import List, Literal
from pydantic import BaseModel, validator, Extra, root_validator
from parser import write_file, elements_json, elements_yaml, elements_files_info
import logging
import re

tree = {}
logger = logging.getLogger('common_logger')

types = Literal["string", "int", "bool", "datetime", "array"]
sub_types = Literal["string", "int", "bool", "datetime"]
constraints = Literal[
    'maxlength', 'minlength', 'pattern', 'cols', 'rows', 'min', 'max', 'format', "pattern", "size", "resize"]
controls = Literal[
    "input_control", "textarea_control", "list_control", "checkbox_control", "number_control", "datetime_control",
    "date_control", "time_control"]


class ConstraintItem(BaseModel):
    value: str
    type: constraints

    class Config:
        orm_mode = True


class ElemInfo(BaseModel):
    value: object
    file_id: str
    type: types
    description: str = None
    sub_type: sub_types = None
    readOnly: bool = False
    display_name: str
    control: controls
    constraints: List[ConstraintItem] = None

    @validator("type")
    def check_type(cls, value_type, values, **kwargs):
        if value_type is None:
            raise TypeError("Type can't be empty")
        if value_type == "string":
            return value_type
        if value_type == "int":
            try:
                int(values["value"])
                return value_type
            except TypeError:
                raise TypeError("Not integer type")
        if value_type == "bool":
            if values["value"] is True or values["value"] is False:
                return value_type
            raise TypeError("Not boolean type")
        if value_type == "double":
            try:
                float(values["value"])
                return value_type
            except TypeError:
                raise TypeError("Not double type")
        if value_type == "datetime":
            try:
                date = maya.parse(values["value"]).datetime()
                values["value"] = date
                return value_type
            except TypeError:
                raise TypeError("Not datetime type")
        if value_type == "array":
            return value_type

    @validator("sub_type")
    def check_sub_type(cls, sub_type, values, **kwargs):
        if values["type"] != "array" and sub_type is not None:
            raise TypeError("sub_type can be not empty only when type is array")
        if values["type"] == "array" and sub_type is None:
            raise TypeError("sub_type can't be empty in array")
        if sub_type == "string":
            return sub_type
        if sub_type == "int":
            for item in values["value"]:
                try:
                    int(item)
                except TypeError:
                    raise TypeError(f"item {item} in array is not integer")
            return sub_type
        if sub_type == "bool":
            for item in values["value"]:
                try:
                    bool(item)
                except TypeError:
                    raise TypeError(f"item {item} in array is not boolean")
            return sub_type
        if sub_type == "double":
            for item in values["value"]:
                try:
                    float(item)
                except TypeError:
                    raise TypeError(f"item {item} in array is not double")
            return sub_type
        if sub_type == "datetime":
            for item in values["value"]:
                try:
                    date = maya.parse(item).datetime()
                    values["value"][values["value"].index(item)] = date
                except TypeError:
                    raise TypeError(f"item {item} in array is not datetime format")
            return sub_type

    @validator("control")
    def check_control(cls, elem_control, values, **kwargs):
        match elem_control:
            case "datetime_control":
                if values["sub_type"] is None:
                    values["value"] = values["value"].replace(tzinfo=None).isoformat()
                else:
                    for item in values["value"]:
                        values["value"][values["value"].index(item)] = item.replace(tzinfo=None).isoformat()
            case "date_control":
                if values["sub_type"] is None:
                    values["value"] = values["value"].replace(tzinfo=None).isoformat()
                else:
                    for item in values["value"]:
                        values["value"][values["value"].index(item)] = item.replace(tzinfo=None).isoformat()
            case "time_control":
                if values["sub_type"] is None:
                    values["value"] = values["value"].replace(tzinfo=None).time().isoformat()
                else:
                    for item in values["value"]:
                        values["value"][values["value"].index(item)] = item.replace(tzinfo=None).time().isoformat()
        return elem_control

    @validator("constraints")
    def check_constraints(cls, elem_constraints, values, **kwargs):
        if values["control"] != "checkbox_control":
            check_allowed_constraints(elem_constraints, values["control"])
            check_constraints_values(elem_constraints, values)
        else:
            if elem_constraints:
                raise ValueError("checkbox_control can't be have constraints")


def check_allowed_constraints(elem_constraints, control):
    for constraint in elem_constraints:
        if constraint.type not in get_control_constraints(control):
            raise ValueError(f"Constraint {constraint.type} not allowed in {control}")


def check_constraints_values(elem_constraints, elem):
    for constraint in elem_constraints:
        match constraint.type:
            case "maxlength":
                try:
                    int(constraint.value)
                except TypeError:
                    raise TypeError(f"In constraint maxlength value must be integer")
            case "minlength":
                try:
                    int(constraint.value)
                except TypeError:
                    raise TypeError(f"In constraint minlength value must be integer")
            case "size":
                try:
                    int(constraint.value)
                except TypeError:
                    raise TypeError(f"In constraint size value must be integer")
            case "pattern":
                if re.match(constraint.value, elem["value"]) is None:
                    raise ValueError(f"The string does not match the regular expression")
            case "min":
                match elem["control"]:
                    case "datetime_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).isoformat()
                        except TypeError:
                            raise TypeError(
                                f"Not datetime value in constraint {constraint.type} when control is {elem['control']}")
                    case "date_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).date().isoformat()
                        except TypeError:
                            raise TypeError(
                                f"Not date value in constraint {constraint.type} when control is {elem['control']}")
                    case "time_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).time().isoformat()
                        except TypeError:
                            raise TypeError(
                                f"Not time value in constraint {constraint.type} when control is {elem['control']}")
                    case "number_control":
                        try:
                            int(constraint.value)
                        except TypeError:
                            raise TypeError(
                                f"Not integer value in constraint {constraint.type} when control is {elem['control']}")

            case "max":
                match elem["control"]:
                    case "datetime_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).isoformat()
                        except TypeError:
                            raise TypeError(
                                f"Not datetime value in constraint {constraint.type} when control is {elem['control']}")
                    case "date_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).date().isoformat()
                        except TypeError:
                            raise TypeError(
                                f"Not date value in constraint {constraint.type} when control is {elem['control']}")
                    case "time_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).time().isoformat()
                        except TypeError:
                            raise TypeError(
                                f"Not time value in constraint {constraint.type} when control is {elem['control']}")
                    case "number_control":
                        try:
                            int(constraint.value)
                        except TypeError:
                            raise TypeError(
                                f"Not integer value in constraint {constraint.type} when control is {elem['control']}")
            case "cols":
                try:
                    int(constraint.value)
                except TypeError:
                    raise TypeError("In constraint cols value must be integer")
            case "rows":
                try:
                    int(constraint.value)
                except TypeError:
                    raise TypeError("In constraint rows value must be integer")
            case "resize":
                try:
                    bool(constraint.value)
                except TypeError:
                    raise TypeError("In constraint resize value must be bool")


def get_control_constraints(control: controls):
    match control:
        case "input_control":
            return ["minlength", "maxlength", "pattern", "size"]
        case "textarea_control":
            return ["minlength", "maxlength", "pattern", "resize", "cols", "rows"]
        case "password_control":
            return ["minlength", "maxlength", "pattern", "size"]
        case "date_control":
            return ["min", "max", "format"]
        case "datetime_control":
            return ["min", "max", "format"]
        case "time_control":
            return ["min", "max", "format"]
        case "number_control":
            return ["min", "max"]


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
                    if elements_yaml.index(elements) < len(elements_files_info):
                        uid = elements_files_info[elements_yaml.index(elements)]["uid"]
                        elem_list.append({key: get_element_info(key, uid)})
    return elem_list


def get_value(input_url: str, uid: str):
    input_url_list = input_url.split("/")
    key = input_url_list[0]
    for elements in elements_json:
        if key in elements.values and elements.uid == uid:
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


def set_value(input_url: str, uid: str, value: str):
    logger.debug(f"post {value} in {input_url}")
    input_url_list = input_url.split("/")
    key = input_url_list[0]
    for elements in elements_json:
        if key in elements.values and elements.uid == uid:
            set_value_in_dict(elements.values, value, input_url_list)
            return write_file(elements.values, elements.path, elements.type, input_url, value)


def get_element_info(input_url, uid: str):
    for elements in elements_yaml:
        for item in elements:
            if input_url in item and elements_files_info[elements_yaml.index(elements)]["uid"] == uid:
                element = item[input_url]
                if len(element) == 0:
                    return None
                render_dict = element["render"]
                render_dict_constraints = render_dict["constraints"]
                render_constraints = []
                if render_dict_constraints:
                    for constraint in render_dict_constraints:
                        for key in constraint:
                            constraint_item = ConstraintItem(value=constraint[key], type=key)
                            render_constraints.append(constraint_item)
                elem_info = ElemInfo(type=element["type"], description=element["description"],
                                     sub_type=element["sub_type"],
                                     readOnly=element["readonly"],
                                     display_name=render_dict["display_name"], control=render_dict["??? control"],
                                     constraints=render_constraints, value=get_value(input_url, uid),
                                     file_id=uid)
                return elem_info
