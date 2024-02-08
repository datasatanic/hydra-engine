import os
import ruamel.yaml
import maya
from typing import List, Literal, Dict
from pydantic import BaseModel, validator, Extra, root_validator, ValidationError

import hydra_engine.filewatcher
from hydra_engine.parser import write_file, HydraParametersInfo, read_hydra_ignore
from hydra_engine.configs import config
import logging
import re

tree = HydraParametersInfo().tree
wizard_tree = HydraParametersInfo().wizard_tree
logger = logging.getLogger('common_logger')

types = Literal["string", "int", "bool", "datetime", "dict", "array", "double"]
sub_types = Literal["string", "int", "bool", "datetime", "dict", "composite", "double"]
constraints = Literal[
    'maxlength', 'minlength', 'pattern', 'cols', 'rows', 'min', 'max', 'format', "size", "resize"]
controls = Literal[
    "input_control", "textarea_control", "checkbox_control", "number_control", "datetime_control",
    "date_control", "time_control", "label_control"]


class ConstraintItem(BaseModel):
    value: str
    type: constraints
    message: str = None

    class Config:
        orm_mode = True


class ElemInfo(BaseModel):
    value: object
    file_id: str
    type: types
    description: str = None
    sub_type: sub_types = None
    sub_type_schema: Dict[str, 'ElemInfo'] = None
    array_sub_type_schema: List['ElemInfo'] = None
    readOnly: bool | Dict[int, bool]
    display_name: str
    control: controls
    constraints: List[ConstraintItem] = None

    @validator("type", pre=True)
    def check_type(cls, value_type, values, **kwargs):
        if values["value"] is None:
            return value_type
        if value_type is None:
            raise TypeError("Type can't be empty")
        elif value_type == "int":
            try:
                int(values["value"])
            except Exception:
                raise TypeError("Not integer type")
        elif value_type == "double":
            try:
                float(values["value"])
            except Exception:
                raise TypeError("Not double type")
        elif value_type == "datetime":
            try:
                date = maya.parse(values["value"]).datetime()
                values["value"] = date
            except Exception:
                raise TypeError("Not datetime type")
        elif value_type == "bool":
            if values["value"] is True or values["value"] is False:
                return value_type
            raise TypeError("Not boolean type")
        return value_type

    @validator("sub_type", pre=True)
    def check_sub_type(cls, sub_type, values, **kwargs):
        if "type" not in values:
            return
        elif values["type"] != "array" and sub_type is not None:
            raise TypeError("sub_type can be not empty only when type is array")
        elif values["type"] == "array" and sub_type is None:
            raise TypeError("sub_type can't be empty in array")
        elif sub_type == "int":
            for item in values["value"]:
                try:
                    if item:
                        int(item)
                except Exception:
                    raise TypeError(f"item {item} in array is not integer")
        elif sub_type == "bool":
            for item in values["value"]:
                try:
                    if item:
                        bool(item)
                except Exception:
                    raise TypeError(f"item {item} in array is not boolean")
        elif sub_type == "double":
            for item in values["value"]:
                try:
                    if item:
                        float(item)
                except Exception:
                    raise TypeError(f"item {item} in array is not double")
        elif sub_type == "datetime":
            for item in values["value"]:
                try:
                    if item:
                        date = maya.parse(item).datetime()
                        values["value"][values["value"].index(item)] = date
                except Exception:
                    raise TypeError(f"item {item} in array is not datetime format")
        return sub_type

    @validator("sub_type_schema", pre=True)
    def check_sub_type_schema(cls, sub_type_schema, values, **kwargs):
        if values.get('type') != "dict" or values.get('type') == "array" and values.get('sub_type') != "composite":
            if sub_type_schema is not None:
                raise ValueError("Parameter with type dict or array with composite type can have sub_type_schema")
        return sub_type_schema

    @validator("control", pre=True)
    def check_control(cls, elem_control, values, **kwargs):
        if "sub_type" not in values or "type" not in values:
            return elem_control
        match elem_control:
            case "datetime_control":
                if not (values["type"] == "datetime" and values["type"] != "array" or values["type"] == "array" and
                        values["sub_type"] == "datetime"):
                    raise TypeError("Only parameters with datetime type can have datetime_control")
                elif values["sub_type"] is None:
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
            case "label_control":
                if not (values["type"] == "dict" or values["type"] == "array" and values["sub_type"] == "composite"):
                    raise TypeError(
                        "Only parameters with dict type or arrays with composite type can have label_control")
            case "input_control":
                if not (values["type"] == "string" and values["type"] != "array" or values["type"] == "array" and
                        values["sub_type"] == "string"):
                    raise TypeError("Only parameters with string type can have input_control")
            case "textarea_control":
                if not (values["type"] == "string" and values["type"] != "array" or values["type"] == "array" and
                        values[
                            "sub_type"] == "string"):
                    raise TypeError("Only parameters with string type can have textarea_control")
            case "number_control":
                if not ((values["type"] == "int" or values["type"] == "double") and values["type"] != "array" or values[
                    "type"] == "array" and (values[
                                                "sub_type"] == "int" or values["sub_type"] == "double")):
                    raise TypeError("Only parameters with int or double type can have number_control")
            case "checkbox_control":
                if not (values["type"] == "bool" and values["type"] != "array" or values["type"] == "array" and values[
                    "sub_type"] == "bool"):
                    raise TypeError("Only parameters with bool type can have checkbox_control")
        return elem_control

    @validator("constraints", pre=True)
    def check_constraints(cls, elem_constraints, values, **kwargs):
        if values.get('type') == "dict" and len(elem_constraints) > 0:
            raise ValueError("Parameter with dict type can't have constraints")
        if values.get('control') != "checkbox_control":
            check_allowed_constraints(elem_constraints, values.get('control'))
            if values["value"] is None:
                return elem_constraints
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
                    if elem.get("type") != "array":
                        if len(elem.get("value")) > maxlength:
                            raise ValueError(f"Value of {elem.get('display_name')} more than max length")
                    else:
                        for value in elem.get("value"):
                            if len(value) > maxlength:
                                raise ValueError(f"Value of {elem.get('display_name')} more than max length")
                except TypeError:
                    raise TypeError(f"In constraint maxlength value must be integer")
            case "minlength":
                try:
                    minlength = int(constraint.value)
                    if elem.get("type") != "array":
                        if len(elem.get("value")) < minlength:
                            raise ValueError(f"Value of {elem.get('display_name')} less than min length")
                    else:
                        for value in elem.get("value"):
                            if len(value) < minlength:
                                raise ValueError(f"Value of array {elem.get('display_name')} less than min length")
                except TypeError:
                    raise TypeError(f"In constraint minlength value must be integer")
            case "size":
                try:
                    int(constraint.value)
                except TypeError:
                    raise TypeError(f"In constraint size value must be integer")
            case "pattern":
                if elem.get("type") != "array":
                    if re.match(constraint.value, elem.get("value")) is None:
                        raise ValueError(f"The string does not match the regular expression")
                else:
                    for value in elem.get("value"):
                        if re.match(constraint.value, value) is None:
                            raise ValueError(f"The string of array does not match the regular expression")
            case "min":
                match elem.get("control"):
                    case "datetime_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).isoformat()
                            if elem.get('type') != "array":
                                min = maya.parse(elem.get("value")).datetime().replace(tzinfo=None)
                                if min < date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem.get('display_name')} less than min value")
                            else:
                                for value in elem.get('value'):
                                    min = maya.parse(value).datetime().replace(tzinfo=None)
                                    if min < date.replace(tzinfo=None):
                                        raise ValueError(
                                            f"Value of array {elem.get('display_name')} less than min value")
                        except TypeError:
                            raise TypeError(
                                f"Not datetime value in constraint {constraint.type} when control is {elem.get('control')}")
                    case "date_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).date().isoformat()
                            if elem.get('type') != "array":
                                min = maya.parse(elem.get('value')).datetime().replace(tzinfo=None)
                                if min < date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem.get('display_name')} less than min value")
                            else:
                                for value in elem.get('value'):
                                    min = maya.parse(value).datetime().replace(tzinfo=None)
                                    if min < date.replace(tzinfo=None):
                                        raise ValueError(
                                            f"Value of array {elem.get('display_name')} less than min value")
                        except TypeError:
                            raise TypeError(
                                f"Not date value in constraint {constraint.type} when control is {elem.get('control')}")
                    case "time_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).time().isoformat()
                            if elem.get('type') != "array":
                                min = maya.parse(elem.get('value')).datetime().replace(tzinfo=None)
                                if min < date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem.get('display_name')} less than min value")
                            else:
                                for value in elem.get('value'):
                                    min = maya.parse(value).datetime().replace(tzinfo=None)
                                    if min < date.replace(tzinfo=None):
                                        raise ValueError(
                                            f"Value of array {elem.get('display_name')} less than min value")
                        except TypeError:
                            raise TypeError(
                                f"Not time value in constraint {constraint.type} when control is {elem.get('control')}")
                    case "number_control":
                        try:
                            min = int(constraint.value)
                            if elem.get('type') != "array":
                                if int(elem.get('value')) < min:
                                    raise ValueError(f"Value of {elem.get('display_name')} less than min value")
                            else:
                                for value in elem.get('value'):
                                    if int(value) < min:
                                        raise ValueError(
                                            f"Value of array {elem.get('display_name')} less than min value")
                        except TypeError:
                            raise TypeError(
                                f"Not integer value in constraint {constraint.type} when control is {elem.get('control')}")
            case "max":
                match elem.get('control'):
                    case "datetime_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).isoformat()
                            if elem.get('type') != "array":
                                max = maya.parse(elem.get('value')).datetime().replace(tzinfo=None)
                                if max > date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem.get('display_name')} more than max value")
                            else:
                                for value in elem.get('value'):
                                    max = maya.parse(value).datetime().replace(tzinfo=None)
                                    if max > date.replace(tzinfo=None):
                                        raise ValueError(
                                            f"Value of array {elem.get('display_name')} more than max value")
                        except TypeError:
                            raise TypeError(
                                f"Not datetime value in constraint {constraint.type} when control is {elem.get('control')}")
                    case "date_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).date().isoformat()
                            if elem.get('type') != "array":
                                max = maya.parse(elem.get('value')).datetime().replace(tzinfo=None)
                                if max > date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem.get('display_name')} more than max value")
                            else:
                                for value in elem.get('value'):
                                    max = maya.parse(value).datetime().replace(tzinfo=None)
                                    if max > date.replace(tzinfo=None):
                                        raise ValueError(
                                            f"Value of array {elem.get('display_name')} more than max value")
                        except TypeError:
                            raise TypeError(
                                f"Not date value in constraint {constraint.type} when control is {elem.get('control')}")
                    case "time_control":
                        try:
                            date = maya.parse(constraint.value).datetime()
                            constraint.value = date.replace(tzinfo=None).time().isoformat()
                            if elem.get('type') != "array":
                                max = maya.parse(elem.get('value')).datetime().replace(tzinfo=None)
                                if max > date.replace(tzinfo=None):
                                    raise ValueError(f"Value of {elem.get('display_name')} more than max value")
                            else:
                                for value in elem.get('value'):
                                    max = maya.parse(value).datetime().replace(tzinfo=None)
                                    if max > date.replace(tzinfo=None):
                                        raise ValueError(
                                            f"Value of array {elem.get('display_name')} more than max value")
                        except TypeError:
                            raise TypeError(
                                f"Not time value in constraint {constraint.type} when control is {elem.get('control')}")
                    case "number_control":
                        try:
                            max = int(constraint.value)
                            if elem.get('type') != "array":
                                if int(elem.get('value')) > max:
                                    raise ValueError(f"Value of {elem.get('display_name')} more than max value")
                            else:
                                for value in elem.get('value'):
                                    if int(value) > max:
                                        raise ValueError(
                                            f"Value of array {elem.get('display_name')} more than max value")
                        except TypeError:
                            raise TypeError(
                                f"Not integer value in constraint {constraint.type} when control is {elem.get('control')}")
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


class Condition(BaseModel):
    key: str
    allow: Dict[str, list]

    def __eq__(self, other):
        if self.key == other.key:
            for k in self.allow:
                if k in other.allow:
                    for el in other.allow[k]:
                        if el in self.allow[k]:
                            continue
                        else:
                            return False
            return True
        else:
            return False


class WizardNode(Node):
    condition: list[Condition]


def add_node(_list, path_id, node_type, condition=None, is_wizard=False):
    level = len(_list)
    if level == 1:
        if not is_wizard:
            node = Node(elem=[], child={}, type=node_type)
        else:
            node = WizardNode(elem=[], child={}, type=node_type, condition=condition)
        node.elem = get_elements(path_id)
        d = {_list[0]: node}
        tree.update(d) if not is_wizard else wizard_tree.update(d)
    else:
        add_node_subtree(tree, 0, _list, path_id, node_type) if not is_wizard else add_node_subtree(wizard_tree, 0,
                                                                                                    _list, path_id,
                                                                                                    node_type,
                                                                                                    condition=condition,
                                                                                                    is_wizard=True)


def add_node_subtree(subtree, j, _list, path_id, node_type, condition=None, is_wizard=False):
    n = len(subtree)
    for i in range(0, n):
        if _list[j] in subtree:
            if subtree[_list[j]].type == "group":
                raise ValueError(f"Node {'/'.join(_list[0:j + 1])} with type group can't have children")
            subtree = subtree[_list[j]].child
            j += 1
            if j == len(_list) - 1:
                if not is_wizard:
                    node = Node(elem=[], child={}, type=node_type)
                else:
                    node = WizardNode(elem=[], child={}, type=node_type, condition=condition)
                node.elem = get_elements(path_id)
                d = {_list[j]: node}
                subtree.update(d)
                return
            add_node_subtree(subtree, j, _list, path_id, node_type, condition, is_wizard)


def add_additional_fields(node_list, additional_key, additional_value, is_wizard=False):
    node = find_node(node_list, is_wizard)
    if additional_key in node.__dict__:
        raise ValueError("Not valid file")
    node.__dict__[additional_key] = additional_value.replace('"', '').strip() if isinstance(additional_value,
                                                                                            str) else additional_value


def find_node(node_list, is_wizard=False):
    subtree = tree if not is_wizard else wizard_tree
    find = {}
    for node in node_list:
        find = subtree[node] if node in subtree else find
        subtree = find.child
    return find


def get_elements(path_id):
    elem_list = []
    elements_meta = HydraParametersInfo().get_elements_metadata()
    elements_files_info = HydraParametersInfo().get_elements_files_info()
    for elements, file_info in zip(elements_meta, elements_files_info):
        for item in elements:
            keys = list(item)
            for key in keys:
                if item[key]["id"] == path_id:
                    uid = file_info["uid"]
                    elem_list.append({key: get_element_info(key, uid)})
    return elem_list


def get_value(input_url: str, uid: str):
    input_url_list = input_url.split("/")
    key = input_url_list[0]
    input_url_list.pop(0)
    for elements in HydraParametersInfo().get_elements_values():
        if key in elements.values and elements.uid == uid:
            return get_value_by_key(elements.values[key], input_url_list)


def get_value_by_key(value, input_url_list):
    if len(input_url_list) == 0:
        return value
    key = input_url_list[0]
    input_url_list.pop(0)
    if key in value:
        return get_value_by_key(value[key], input_url_list)
    else:
        logger.error("Key not exist")


def set_value_in_dict(elements, value, input_url_list):
    while len(input_url_list) > 1:
        elements = elements[input_url_list[0]]
        input_url_list.pop(0)
    if elements[input_url_list[0]] != value:
        elements[input_url_list[0]] = update_parameter_value(elements[input_url_list[0]], value)
        HydraParametersInfo().was_modified = True


def update_parameter_value(element, value):
    if isinstance(element, dict):
        element.update(
            {key: update_parameter_value(element[key], value[key]) for key in element if element[key] != value[key]})
        return element
    elif isinstance(element, list):
        if element != value:
            element_len = len(element)
            value_len = len(value)
            if value_len == 0:
                element = None
                return element
            if element_len > value_len:
                element = element[:len(value)]
            elif element_len < value_len:
                for val in value[element_len:]:
                    element.append(val)
            for index, (el, val) in enumerate(zip(element, value)):
                if el != val:
                    element[index] = update_parameter_value(el, val)
            return element
    else:
        if element != value:
            return value


def set_value(input_url: str, uid: str, value: object):
    logger.debug(f"post {value} in {input_url}")
    input_url_list = input_url.split("/")
    key = input_url_list[0]
    for elements in HydraParametersInfo().get_elements_values():
        if key in elements.values and elements.uid == uid:
            set_value_in_dict(elements.values, value, input_url_list)
            write_file(elements.values, elements.path, elements.type, input_url, value)
            print(hydra_engine.filewatcher.file_event.is_set())
            if hydra_engine.filewatcher.file_event.is_set():
                hydra_engine.filewatcher.file_event.wait()
            return


def get_element_info(input_url, uid: str):
    elements_meta = HydraParametersInfo().get_elements_metadata()
    elements_files_info = HydraParametersInfo().get_elements_files_info()
    for elements, file_info in zip(elements_meta, elements_files_info):
        for item in elements:
            if input_url in item and file_info["uid"] == uid:
                element = item[input_url]
                if len(element) == 0:
                    return None
                value = get_value(input_url, uid)
                elem_info = generate_elem_info(value, element, uid, input_url, True)
                return elem_info


def generate_elem_info(value, element, uid, path, is_log):
    try:
        render_constraints = []
        render_dict = element.get('render')
        if render_dict:
            render_dict_constraints = render_dict.get('constraints')
            if render_dict_constraints:
                for constraint in render_dict_constraints:
                    for key in constraint:
                        constraint_item = ConstraintItem(value=constraint[key].get('value'), type=key,
                                                         message=constraint[key].get('message'))
                        render_constraints.append(constraint_item)
        elem_info = ElemInfo(value=value, type=element.get('type'),
                             description=element.get('description'),
                             sub_type=element.get('sub_type'),
                             sub_type_schema=None,
                             readOnly=element["readonly"] if "readonly" in element else False,
                             display_name=render_dict.get('display_name') if render_dict else None,
                             control=render_dict.get('control') if render_dict else None,
                             constraints=render_constraints,
                             file_id=uid)
        if element.get("sub_type_schema") is not None:
            sub_type_schema = element.get("sub_type_schema")
            if element.get("type") == "array":
                elem_info.array_sub_type_schema = []
                value = [] if value is None else value
                for index, el in enumerate(value):
                    is_element_none = el is None
                    d = {}
                    for key, metadata in element["sub_type_schema"].items():
                        if key in el:
                            d.update({
                                key: generate_elem_info(
                                    el[key] if not is_element_none else metadata["default_value"],
                                    metadata, uid, f"{path}/{key}", False
                                )
                            })
                    if is_element_none:
                        value[index] = {key: metadata["default_value"] for key, metadata in
                                        element["sub_type_schema"].items()}
                    elem_info.array_sub_type_schema.append(d)
                elem_info.sub_type_schema = {}
                for key, metadata in element["sub_type_schema"].items():
                    elem_info.sub_type_schema.update({
                        key: generate_elem_info(metadata["default_value"], metadata, uid, f"{path}/{key}", is_log)
                    })
            else:
                if value:
                    if isinstance(sub_type_schema, dict):
                        elem_info.sub_type_schema = {
                            key: generate_elem_info(value[key], metadata, uid, f"{path}/{key}", is_log)
                            for key, metadata in sub_type_schema.items()
                        }
                    else:
                        raise TypeError("Type of field sub_type_schema must be dict")
                else:
                    elem_info.value = {}
                    elem_info.sub_type_schema = {}
                    for key, metadata in element["sub_type_schema"].items():
                        elem_info.sub_type_schema.update({
                            key: generate_elem_info(metadata["default_value"], metadata, uid, f"{path}/{key}", True)
                        })
                        elem_info.value.update({key: metadata["default_value"]})
        return elem_info
    except ValidationError as e:
        if is_log:
            value_instance = next((item for item in HydraParametersInfo().elements_values if item.uid == uid), None)
            file_info = next(
                (item for item in HydraParametersInfo().elements_files_info if item["path"] == value_instance.path),
                None)
            for error in e.errors():
                for loc in error["loc"]:
                    logger.error(
                        f"{file_info['meta_path']} validation error in metadata of parameter({path}),line:{element.lc.line}, field: {loc}, message: {error['msg']}")
    except TypeError as e:
        if is_log:
            value_instance = next((item for item in HydraParametersInfo().elements_values if item.uid == uid), None)
            file_info = next(
                (item for item in HydraParametersInfo().elements_files_info if item["path"] == value_instance.path),
                None)
            logger.error(
                f"{file_info['meta_path']} validation error in metadata of parameter({path}),line:{element.lc.line}, field: sub_type_schema, message: {e}")


def filter_tree(all_tree):
    """
        Deletes empty nodes with no child elements
    """
    tree_filter = all_tree
    keys = list(tree_filter)
    for key in keys:
        tree_filter[key].elem.clear()
        if tree_filter[key].type == "group":
            tree_filter.pop(key)
        else:
            filter_tree(tree_filter[key].child)
    return tree_filter


def find_form(path, all_tree, is_wizard=False):
    """
        Find child forms and groups of current form
    """
    name = path[0]
    if name in all_tree:
        if len(path) > 1:
            path.remove(name)
            return find_form(path, all_tree[name].child)
        else:
            for child_name in all_tree[name].child:
                if all_tree[name].child[child_name].type == "form":
                    all_tree[name].child[child_name].elem.clear()
                    all_tree[name].child[child_name].child.clear()
                    if is_wizard:
                        condition = all_tree[name].child[child_name].condition
                        [cond.allow.clear() for cond in condition]
            return {name: all_tree[name]}


yaml = ruamel.yaml.YAML(typ="rt")
base_dir = os.path.dirname(os.path.abspath(__file__))


def update_wizard_meta(directory: str, arch_name):
    file = open(os.path.join(config.filespath, "wizard.meta"), 'r+')
    ignore_dirs, ignore_extension = read_hydra_ignore()
    wizard_data = yaml.load(file)
    last_id = None
    last_path = None
    last_dir = None
    for root, dirs, files in os.walk(directory):
        arch_file = open(os.path.join(config.filespath, f"_framework/arch/{arch_name}.yml"), 'r')
        site_names = list(map(lambda x: x["name"], yaml.load(arch_file)["sites"]))
        arch_file.close()
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        dirs.sort(key=lambda x: site_names.index(x) if x in site_names else float('inf'))
        for name in files:
            if name.endswith(
                    "meta") and name != config.wizard_filename and name != config.tree_filename:
                last_key, last_value = list(wizard_data.items())[-1]
                file_path = os.path.join(root, name)
                directory_path = os.path.dirname(file_path)
                files_in_directory = list(
                    filter(lambda filename: filename.endswith("meta"), os.listdir(directory_path)))
                _dir = os.path.basename(os.path.dirname(os.path.dirname(file_path)))
                if last_id is None:
                    last_id = last_value["id"]
                else:
                    last_id += 1
                if last_path is None:
                    last_path = f"root/{name.replace('.yml.meta', '')}"
                    wizard_form = {
                        last_path: {"display_name": name.replace('.yml.meta', '').title(),
                                    "description": "", "type": "form", "sub_type": "config",
                                    "id": last_id + 1}}
                    if last_path not in wizard_data:
                        file.write('\n')
                        yaml.dump(wizard_form, file)
                else:
                    if _dir != last_dir:
                        last_dir = _dir
                        last_path += "/" + _dir
                        wizard_form = {
                            last_path: {"display_name": _dir.title(),
                                        "description": "", "type": "form", "sub_type": "site",
                                        "id": last_id + 1}}
                        if last_path not in wizard_data:
                            file.write('\n')
                            yaml.dump(wizard_form, file)
                        last_id += 1
                    path = last_path + "/" + name.replace('.yml.meta', '')
                    wizard_group = {
                        path: {"display_name": name.replace('.yml.meta', '').title(),
                               "description": "", "type": "form", "sub_type": "config",
                               "id": last_id + 1, "action": "deploy" if name == files_in_directory[
                                -1] and name != "global.yml.meta" else None}}
                    if last_path not in wizard_data:
                        file.write('\n')
                        yaml.dump(wizard_group, file)
    file.close()


def check_validate_parameter(input_url, value, uid, node):
    parameter = None
    for el in node.elem:
        if input_url in el:
            parameter = el[input_url]
    if parameter:
        try:
            check_sub_type_schema_validate(parameter, value, uid, input_url)
            return True
        except ValidationError as e:
            return str(e)
        except ValueError as e:
            return str(e)
    else:
        for key in node.child:
            if not check_validate_parameter(input_url, value, uid, node.child[key]):
                return False
        return True


def check_sub_type_schema_validate(parameter, value, uid, input_url):
    if value is None:
        raise ValueError(f"Empty value for parameter with path {input_url}")
    else:
        if parameter.type != "array" and parameter.type != "dict" and str(value).strip() == '':
            raise ValueError(f"Empty value for parameter with path {input_url}")
    elem_info = ElemInfo(value=value, type=parameter.type,
                         description=parameter.description,
                         sub_type=parameter.sub_type,
                         sub_type_schema=None,
                         readOnly=parameter.readOnly,
                         display_name=parameter.display_name,
                         control=parameter.control,
                         constraints=parameter.constraints,
                         file_id=uid)
    if parameter.sub_type_schema is not None:
        for key, metadata in parameter.sub_type_schema.items():
            if isinstance(value, dict):
                check_sub_type_schema_validate(metadata, value[key], uid, f"{input_url}/{key}")
            elif isinstance(value, list):
                for el in value:
                    check_sub_type_schema_validate(metadata, el[key], uid, f"{input_url}/{key}")
    return elem_info
