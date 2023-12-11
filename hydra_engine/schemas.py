import json
import yaml
import maya
from typing import List, Literal
from pydantic import BaseModel, validator, Extra, root_validator
from hydra_engine.parser import write_file, HydraParametersInfo
import logging
import re

tree = HydraParametersInfo().tree
logger = logging.getLogger('common_logger')

types = Literal["string", "int", "bool", "datetime", "range", "array"]
sub_types = Literal["string", "int", "bool", "datetime", "range"]
constraints = Literal[
    'maxlength', 'minlength', 'pattern', 'cols', 'rows', 'min', 'max', 'format', "size", "resize"]
controls = Literal[
    "input_control", "textarea_control", "list_control", "checkbox_control", "number_control", "datetime_control",
    "date_control", "time_control", "range_control"]


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

    @validator("type", pre=True)
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
        if value_type == "range":
            try:
                int(values["value"]["from"])
                int(values["value"]["to"])
                return value_type
            except TypeError:
                raise TypeError("Not range type")
        if value_type == "array":
            return value_type

    @validator("sub_type", pre=True)
    def check_sub_type(cls, sub_type, values, **kwargs):
        if "type" not in values:
            return
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
        if sub_type == "range":
            for item in values["value"]:
                try:
                    int(item["from"])
                    int(item["to"])
                except TypeError:
                    raise TypeError(f"item {item} in array is not range")
            return sub_type

    @validator("control", pre=True)
    def check_control(cls, elem_control, values, **kwargs):
        if "sub_type" not in values:
            return
        match elem_control:
            case "datetime_control":
                if values["sub_type"] is None:
                    values["value"] = values["value"].replace(tzinfo=None).isoformat()
                else:
                    for item in values["value"]:
                        values["value"][values["value"].index(item)] = item.replace(tzinfo=None).isoformat()
            case "date_control":
                if values["sub_type"] is None:
                    values["value"] = values["value"].replace(tzinfo=None).date().isoformat()
                else:
                    for item in values["value"]:
                        values["value"][values["value"].index(item)] = item.replace(tzinfo=None).date().isoformat()
            case "time_control":
                if values["sub_type"] is None:
                    values["value"] = values["value"].replace(tzinfo=None).time().isoformat()
                else:
                    for item in values["value"]:
                        values["value"][values["value"].index(item)] = item.replace(tzinfo=None).time().isoformat()
        return elem_control

    @validator("constraints", pre=True)
    def check_constraints(cls, elem_constraints, values, **kwargs):
        if "control" not in values:
            return
        if values["control"] != "checkbox_control":
            check_allowed_constraints(elem_constraints, values["control"])
            check_constraints_values(elem_constraints, values)
            return elem_constraints
        else:
            if elem_constraints:
                raise ValueError("checkbox_control can't be have constraints")
            return elem_constraints


def check_allowed_constraints(elem_constraints, control):
    for constraint in elem_constraints:
        if constraint.type not in get_control_constraints(control):
            raise ValueError(f"Constraint {constraint.type} not allowed in {control}")


def check_constraints_values(elem_constraints, elem):
    for constraint in elem_constraints:
        match constraint.type:
            case "maxlength":
                try:
                    maxlength = int(constraint.value)
                    if elem["type"] != "array":
                        if len(elem["value"]) > maxlength:
                            raise ValueError(f"Value of {elem['display_name']} more than max length")
                    else:
                        for value in elem["value"]:
                            if len(value) > maxlength:
                                raise ValueError(f"Value of {elem['display_name']} more than max length")
                except TypeError:
                    raise TypeError(f"In constraint maxlength value must be integer")
            case "minlength":
                try:
                    minlength = int(constraint.value)
                    if elem["type"] != "array":
                        if len(elem["value"]) < minlength:
                            raise ValueError(f"Value of {elem['display_name']} less than min length")
                    else:
                        for value in elem["value"]:
                            if len(value) < minlength:
                                raise ValueError(f"Value of array {elem['display_name']} less than min length")
                except TypeError:
                    raise TypeError(f"In constraint minlength value must be integer")
            case "size":
                try:
                    int(constraint.value)
                except TypeError:
                    raise TypeError(f"In constraint size value must be integer")
            case "pattern":
                if elem["type"] != "array":
                    if re.match(constraint.value, elem["value"]) is None:
                        raise ValueError(f"The string does not match the regular expression")
                else:
                    for value in elem["value"]:
                        if re.match(constraint.value, value) is None:
                            raise ValueError(f"The string of array does not match the regular expression")
            case "min":
                match elem["control"]:
                    case "datetime_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).isoformat()
                            if elem["type"] != "array":
                                min = maya.parse(elem["value"]).datetime().replace(tzinfo=None)
                                if min < date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem['display_name']} less than min value")
                            else:
                                for value in elem["value"]:
                                    min = maya.parse(value).datetime().replace(tzinfo=None)
                                    if min < date.replace(tzinfo=None):
                                        raise ValueError(f"Value of array {elem['display_name']} less than min value")
                        except TypeError:
                            raise TypeError(
                                f"Not datetime value in constraint {constraint.type} when control is {elem['control']}")
                    case "date_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).date().isoformat()
                            if elem["type"] != "array":
                                min = maya.parse(elem["value"]).datetime().replace(tzinfo=None)
                                if min < date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem['display_name']} less than min value")
                            else:
                                for value in elem["value"]:
                                    min = maya.parse(value).datetime().replace(tzinfo=None)
                                    if min < date.replace(tzinfo=None):
                                        raise ValueError(f"Value of array {elem['display_name']} less than min value")
                        except TypeError:
                            raise TypeError(
                                f"Not date value in constraint {constraint.type} when control is {elem['control']}")
                    case "time_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).time().isoformat()
                            if elem["type"] != "array":
                                min = maya.parse(elem["value"]).datetime().replace(tzinfo=None)
                                if min < date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem['display_name']} less than min value")
                            else:
                                for value in elem["value"]:
                                    min = maya.parse(value).datetime().replace(tzinfo=None)
                                    if min < date.replace(tzinfo=None):
                                        raise ValueError(f"Value of array {elem['display_name']} less than min value")
                        except TypeError:
                            raise TypeError(
                                f"Not time value in constraint {constraint.type} when control is {elem['control']}")
                    case "number_control":
                        try:
                            min = int(constraint.value)
                            if elem["type"] != "array":
                                if int(elem["value"]) < min:
                                    raise ValueError(f"Value of {elem['display_name']} less than min value")
                            else:
                                for value in elem["value"]:
                                    if int(value) < min:
                                        raise ValueError(f"Value of array {elem['display_name']} less than min value")
                        except TypeError:
                            raise TypeError(
                                f"Not integer value in constraint {constraint.type} when control is {elem['control']}")
            case "max":
                match elem["control"]:
                    case "datetime_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).isoformat()
                            if elem["type"] != "array":
                                max = maya.parse(elem["value"]).datetime().replace(tzinfo=None)
                                if max > date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem['display_name']} more than max value")
                            else:
                                for value in elem["value"]:
                                    max = maya.parse(value).datetime().replace(tzinfo=None)
                                    if max > date.replace(tzinfo=None):
                                        raise ValueError(f"Value of array {elem['display_name']} more than max value")
                        except TypeError:
                            raise TypeError(
                                f"Not datetime value in constraint {constraint.type} when control is {elem['control']}")
                    case "date_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).date().isoformat()
                            if elem["type"] != "array":
                                max = maya.parse(elem["value"]).datetime().replace(tzinfo=None)
                                if max > date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem['display_name']} more than max value")
                            else:
                                for value in elem["value"]:
                                    max = maya.parse(value).datetime().replace(tzinfo=None)
                                    if max > date.replace(tzinfo=None):
                                        raise ValueError(f"Value of array {elem['display_name']} more than max value")
                        except TypeError:
                            raise TypeError(
                                f"Not date value in constraint {constraint.type} when control is {elem['control']}")
                    case "time_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).time().isoformat()
                            if elem["type"] != "array":
                                max = maya.parse(elem["value"]).datetime().replace(tzinfo=None)
                                if max > date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem['display_name']} more than max value")
                            else:
                                for value in elem["value"]:
                                    max = maya.parse(value).datetime().replace(tzinfo=None)
                                    if max > date.replace(tzinfo=None):
                                        raise ValueError(f"Value of array {elem['display_name']} more than max value")
                        except TypeError:
                            raise TypeError(
                                f"Not time value in constraint {constraint.type} when control is {elem['control']}")
                    case "number_control":
                        try:
                            max = int(constraint.value)
                            if elem["type"] != "array":
                                if int(elem["value"]) > max:
                                    raise ValueError(f"Value of {elem['display_name']} more than max value")
                            else:
                                for value in elem["value"]:
                                    if int(value) > max:
                                        raise ValueError(f"Value of array {elem['display_name']} more than max value")
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


class ParameterSaveInfo(BaseModel):
    input_url: str
    value: object
    file_id: str


class Node(BaseModel):
    child: dict = {}
    elem: List = []
    type: str

    class Config:
        extra = Extra.allow


def add_node(_list, path_id, node_type):
    level = len(_list)
    if level == 1:
        node = Node(elem=[], child={}, type=node_type)
        node.elem = get_elements(path_id)
        d = {_list[0]: node}
        tree.update(d)
    else:
        add_node_subtree(tree, 0, _list, path_id, node_type)


def add_node_subtree(subtree, j, _list, path_id, node_type):
    n = len(subtree)
    for i in range(0, n):
        if _list[j] in subtree:
            if subtree[_list[j]].type == "group":
                raise ValueError(f"Node {'/'.join(_list[0:j + 1])} with type group can't have children")
            subtree = subtree[_list[j]].child
            j += 1
            if j == len(_list) - 1:
                node = Node(elem=[], child={}, type=node_type)
                node.elem = get_elements(path_id)
                d = {_list[j]: node}
                subtree.update(d)
                return
            add_node_subtree(subtree, j, _list, path_id, node_type)


def add_additional_fields(node_list, additional_key, additional_value):
    node = find_node(node_list)
    if additional_key in node.__dict__:
        raise ValueError("Not valid file")
    node.__dict__[additional_key] = additional_value.replace('"', '').strip()


def find_node(node_list):
    subtree = tree
    find = {}
    for node in node_list:
        find = subtree[node] if node in subtree else find
        subtree = find.child
    return find


def get_elements(path_id):
    elem_list = []
    elements_meta = HydraParametersInfo().get_elements_metadata()
    elements_files_info = HydraParametersInfo().get_elements_files_info()
    for elements in elements_meta:
        for item in elements:
            keys = list(item)
            for key in keys:
                if item[key]["id"] == path_id:
                    if elements_meta.index(elements) < len(elements_files_info):
                        uid = elements_files_info[elements_meta.index(elements)]["uid"]
                        elem_list.append({key: get_element_info(key, uid)})
    return elem_list


def get_value(input_url: str, uid: str):
    input_url_list = input_url.split("/")
    key = input_url_list[0]
    for elements in HydraParametersInfo().get_elements_values():
        if key in elements.values and elements.uid == uid:
            return find_value_in_dict(elements.values, input_url_list)


def find_value_in_dict(elements, input_url_list):
    while len(input_url_list) > 0:
        elements = elements[input_url_list[0]]
        input_url_list.pop(0)
    return elements


def set_value_in_dict(elements, value, input_url_list, file_type):
    while len(input_url_list) > 1:
        elements = elements[input_url_list[0]]
        input_url_list.pop(0)
    if file_type == "yaml":
        elements[input_url_list[0]] = yaml.safe_load(value)
    else:
        elements[input_url_list[0]] = value


def set_value(input_url: str, uid: str, value: object):
    logger.debug(f"post {value} in {input_url}")
    input_url_list = input_url.split("/")
    key = input_url_list[0]
    for elements in HydraParametersInfo().get_elements_values():
        if key in elements.values and elements.uid == uid:
            set_value_in_dict(elements.values, value, input_url_list, elements.type)
            return write_file(elements.values, elements.path, elements.type, input_url, value)


def get_element_info(input_url, uid: str):
    elements_meta = HydraParametersInfo().get_elements_metadata()
    elements_files_info = HydraParametersInfo().get_elements_files_info()
    for elements in elements_meta:
        for item in elements:
            if input_url in item and elements_files_info[elements_meta.index(elements)]["uid"] == uid:
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
                try:
                    elem_info = ElemInfo(value=get_value(input_url, uid), type=element["type"],
                                         description=element["description"],
                                         sub_type=element["sub_type"],
                                         readOnly=element["readonly"],
                                         display_name=render_dict["display_name"], control=render_dict["control"],
                                         constraints=render_constraints,
                                         file_id=uid)
                except Exception as e:
                    logger.error(
                        f"Error {e} in file {elements_files_info[elements_meta.index(elements)]['path']} in parameter {input_url}")
                return elem_info
