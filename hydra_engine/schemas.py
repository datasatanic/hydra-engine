import os
import ruamel.yaml
import maya
import markdown
import hashlib
from ruamel.yaml.scalarstring import PlainScalarString, SingleQuotedScalarString, DoubleQuotedScalarString
from typing import List, Literal, Dict
from pydantic import BaseModel, validator, Extra, root_validator, ValidationError

from hydra_engine.parser import write_file, HydraParametersInfo, WizardInfo, read_hydra_ignore, \
    uncomment_all_array_elements
from hydra_engine.configs import config, yaml_config
import logging
import re

tree = HydraParametersInfo().tree
wizard_tree = HydraParametersInfo().wizard_tree
logger = logging.getLogger('common_logger')

types = Literal[
    "string", "string-single-quoted", "string-double-quoted", "int", "bool", "datetime", "dict", "array", "double"]
sub_types = Literal[
    "string", "string-single-quoted", "string-double-quoted", "int", "bool", "datetime", "dict", "composite", "double"]
constraints = Literal[
    'maxlength', 'minlength', 'pattern', 'cols', 'rows', 'min', 'max', 'format', "size", "resize"]
controls = Literal[
    "input_control", "textarea_control", "checkbox_control", "number_control", "datetime_control",
    "date_control", "time_control", "label_control", "password_control"]


class CommentItem(BaseModel):
    url: str
    file_id: str
    is_comment: bool


class Arch(BaseModel):
    arch_name: str
    status: str


class Site(BaseModel):
    site_name: str
    step_number: str
    status: str


class WizardState(BaseModel):
    current_step: str
    arch: Arch
    sites: List[Site]


class ConstraintItem(BaseModel):
    value: str
    type: constraints
    message: str = None

    class Config:
        orm_mode = True


class ElemInfo(BaseModel):
    value: object
    placeholder: object
    autocomplete: object = None
    file_id: str
    type: types
    description: str = None
    sub_type: sub_types = None
    sub_type_schema: Dict[str, 'ElemInfo'] = None
    array_sub_type_schema: List['ElemInfo'] = None
    readOnly: bool | Dict[int, bool]
    disable: bool = False
    additional: bool = False
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
        if values.get('type') != "dict" or values.get('type') != "array":
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
                if not ("string" in values["type"] and values["type"] != "array" or values["type"] == "array" and
                        "string" in values["sub_type"]):
                    raise TypeError("Only parameters with string type can have input_control")
            case "textarea_control":
                if not ("string" in values["type"] and values["type"] != "array" or values["type"] == "array" and
                        "string" in values["sub_type"]):
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
            case "password_control":
                if not ("string" in values["type"] and values["type"] != "array" or values["type"] == "array" and
                        "string" in values["sub_type"]):
                    raise TypeError("Only parameters with string type can have password_control")
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
        if file_info["uid"] == path_id:
            for item in elements:
                keys = list(item)
                for key in keys:
                    elem_list.append({key: get_element_info(key, path_id)})
    return elem_list


def get_value(input_url: str, uid: str):
    input_url_list = input_url.split("/")
    key = input_url_list[0]
    for elements in HydraParametersInfo().get_elements_values():
        if key in elements.values and elements.uid == uid:
            return get_value_by_key(elements.values, input_url_list)


def get_value_by_key(value, input_url_list, comment=None):
    if len(input_url_list) == 0:
        return value, comment
    key = input_url_list[0]
    input_url_list.pop(0)
    if key in value:
        if hasattr(value, "ca") and key in value.ca.items and value.ca.items[key][2]:
            comment = value.ca.items[key][2].value.split("\n")[0]
        return get_value_by_key(value[key], input_url_list, comment)
    else:
        logger.error("Key not exist")


def set_value_in_dict(elements, value, input_url_list):
    while len(input_url_list) > 1:
        elements = elements[input_url_list[0]]
        input_url_list.pop(0)
    elements[input_url_list[0]] = update_parameter_value(elements[input_url_list[0]], value)
    update_comment(elements, input_url_list[0])
    HydraParametersInfo().was_modified = True


def get_comment_with_text(data):
    for el in data:
        if el is not None and not isinstance(el, list):
            if "[ ] CHANGEME" in el.value.split("\n")[0]:
                return el.value
    return None


def update_comment(element, key):
    if hasattr(element, "ca"):
        comment = element.ca.items.get(key, None)
        if comment is not None:
            comment_value = get_comment_with_text(comment)
            if comment_value is not None:
                start_index = comment_value.index("[ ] CHANGEME")
                modified_comment = comment_value[:start_index + 1] + 'X' + comment_value[start_index + 2:]
                for item in element.ca.items[key]:
                    if item:
                        item.value = modified_comment
                        break


def update_parameter_value(element, value):
    if isinstance(element, dict):
        for key in element:
            element.update(
                {key: update_parameter_value(element[key], value[key])})
            update_comment(element, key)
        return element
    elif isinstance(element, list):
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
            element[index] = update_parameter_value(el, val)
            update_comment(element, index)
        return element
    else:
        return value


def set_value(input_url: str, uid: str, value: object):
    logger.debug(f"post {value} in {input_url}")
    input_url_list = input_url.split("/")
    key = input_url_list[0]
    for elements in HydraParametersInfo().get_elements_values():
        if key in elements.values and elements.uid == uid:
            set_value_in_dict(elements.values, value, input_url_list)
            write_file(elements.values, elements.path, elements.type, input_url, value)
            break


'''
Функция для получения информации о параметре конфигурационного файла, в том числе метаданных
'''


def get_element_info(input_url, uid: str):
    elements_meta = HydraParametersInfo().get_elements_metadata()
    elements_files_info = HydraParametersInfo().get_elements_files_info()
    for elements, file_info in zip(elements_meta, elements_files_info):
        if file_info["uid"] == uid:
            for item in elements:
                if input_url in item:
                    element = item[input_url]
                    if len(element) == 0:
                        return None
                    value, comment = get_value(input_url, uid)
                    elem_info = generate_elem_info(value, element, uid, input_url, True, comment)
                    return elem_info


'''
Функция для создания объекта ElemInfo
'''


def generate_elem_info(value, element, uid, path, is_log, comment=None):
    try:
        '''
        Обработка данных об ограничених параметра
        '''
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
        autocomplete = None
        '''
        Обработка комментария [ ] CHANGEME
        '''
        if (comment is not None and "[ ] CHANGEME" in comment and element.get("type") != "array" and element.get(
                "type") != "dict" and element.get("type") != "bool"):
            autocomplete = value
            value = None
        '''
        Инициализация объекта ElemInfo
        '''
        elem_info = ElemInfo(value=value, placeholder=element.get('default_value'), autocomplete=autocomplete,
                             type=element.get('type'),
                             description=markdown.markdown(element.get('description')) if element.get(
                                 'description') is not None and element.get('description') != "" else element.get(
                                 'description'),
                             sub_type=element.get('sub_type'),
                             sub_type_schema=None,
                             readOnly=element["readonly"] if "readonly" in element else False,
                             additional=element.get('additional', False),
                             disable=element.get("disable", False),
                             display_name=render_dict.get('display_name') if render_dict else None,
                             control=render_dict.get('control') if render_dict else None,
                             constraints=render_constraints,
                             file_id=uid)
        if element.get(
                "sub_type_schema") is not None:  # обработка дочерней схемы параметра(для словарей и массивов объектов)
            sub_type_schema = element.get("sub_type_schema")
            if element.get("type") == "array":
                elem_info.array_sub_type_schema = []
                value = [] if value is None else value
                for index, el in enumerate(value):
                    is_element_none = el is None
                    d = {}
                    is_disable = False
                    if hasattr(el, "ca") and hasattr(el.ca, "items"):  # закомментирован ли элемент массива
                        keys = list(el.ca.items.keys())
                        if len(keys) > 0 and "# foot_comment" in el.ca.items[keys[-1]][2].value:
                            is_disable = True
                    for key, metadata in element[
                        "sub_type_schema"].items():  # формирование объектов ElemInfo для элементов массива
                        comment = None
                        metadata["disable"] = is_disable
                        if el is not None and hasattr(el, "ca") and key in el.ca.items:
                            comment = el.ca.items[key][2].value.split("\n")[0]
                        d.update({
                            key: generate_elem_info(
                                el.get(key, None),
                                metadata, uid, f"{path}/{key}", False, comment
                            )
                        })
                    if is_element_none:
                        value[index] = {key: None for key, metadata in
                                        element["sub_type_schema"].items()}
                    elem_info.array_sub_type_schema.append(d)
                elem_info.sub_type_schema = {}
                for key, metadata in element["sub_type_schema"].items():
                    elem_info.sub_type_schema.update({
                        key: generate_elem_info(None, metadata, uid, f"{path}/{key}", is_log)
                    })
            else:
                if isinstance(sub_type_schema, dict):
                    elem_info.sub_type_schema = {}
                    for key, metadata in sub_type_schema.items():  # формирование объектов ElemInfo для вложенных элементов словаря
                        sub_comment = None
                        if value is not None and hasattr(value, "ca") and key in value.ca.items:
                            sub_comment = get_comment_with_text(value.ca.items[key])
                        elem_info.sub_type_schema.update(
                            {key: generate_elem_info(value.get(key) if value is not None else None, metadata, uid,
                                                     f"{path}/{key}", is_log, sub_comment if sub_comment else comment)}
                        )
                else:
                    raise TypeError("Type of field sub_type_schema must be dict")
        elif elem_info.type == "array" and element.get(
                "sub_type_schema") is None:  # обработка данных для обычного массива
            value = [] if value is None else value
            '''
            Создание объектов ElemInfo для элементов массива
            '''
            sub_elem_info = ElemInfo(value=None, placeholder="", autocomplete=autocomplete,
                                     # генерация шаблонного объекта ElemInfo
                                     type=element.get('sub_type'),
                                     description="",
                                     sub_type=None,
                                     sub_type_schema=None,
                                     readOnly=element["readonly"] if "readonly" in element else False,
                                     additional=False,
                                     disable=element.get("disable", False),
                                     display_name="",
                                     control=render_dict.get('control') if render_dict else None,
                                     constraints=render_constraints,
                                     file_id=uid)
            elem_info.sub_type_schema = {"hydra_array_element": sub_elem_info}
            elem_info.array_sub_type_schema = []
            for index, el in enumerate(value):
                el_auto_complete = None
                if hasattr(value, "ca") and index in value.ca.items:
                    for ca in value.ca.items[index]:
                        if ca and "[ ] CHANGEME" in ca.value.split("\n")[0]:  # проверка комментария [ ] CHANGEME
                            el_auto_complete = el
                            el = None
                            break
                # Создание объекта ElemInfo с значением элемента массива для array_sub_type_schema
                elem_info_el = ElemInfo(value=el, placeholder="", autocomplete=el_auto_complete,
                                        type=element.get('sub_type'),
                                        description="",
                                        sub_type=None,
                                        sub_type_schema=None,
                                        readOnly=element["readonly"] if "readonly" in element else False,
                                        additional=False,
                                        disable=False,
                                        display_name="",
                                        control=render_dict.get('control') if render_dict else None,
                                        constraints=render_constraints,
                                        file_id=uid)
                elem_info.array_sub_type_schema.append({"hydra_array_element": elem_info_el})
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


'''
Функция для поиска формы в дереве по пути
'''


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


base_dir = os.path.dirname(os.path.abspath(__file__))

'''
Функция для обновления файла wizard.meta после инициализации архитектуры
'''


def update_wizard_meta(directory: str, arch_name):
    file = open(os.path.join(config.filespath, "wizard.meta"), 'r')
    ignore_dirs, ignore_extension = read_hydra_ignore()
    wizard_data = yaml_config.yaml.load(file)
    last_path = None
    last_dir = None
    for root, dirs, files in os.walk(directory):
        arch_file = open(os.path.join(config.filespath, f"_framework/arch/{arch_name}.yml"), 'r')
        site_names = list(map(lambda x: x["name"], yaml_config.yaml.load(arch_file)["sites"]))
        arch_file.close()
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        dirs.sort(key=lambda x: site_names.index(x) if x in site_names else float('inf'))
        files.sort()
        for name in files:
            if name.endswith(
                    "meta") and name != config.wizard_filename and name != config.tree_filename:
                file_path = os.path.join(root, name)
                directory_path = os.path.dirname(file_path)
                files_in_directory = list(
                    filter(lambda filename: filename.endswith("meta"), os.listdir(directory_path)))
                files_in_directory.sort()
                _dir = os.path.basename(os.path.dirname(os.path.dirname(file_path)))
                '''
                Добавление новых шагов визарда
                '''
                if last_path is None:
                    last_path = f"root/{name.replace('.yml.meta', '')}"
                    wizard_form = {
                        last_path: {"display_name": name.replace('.yml.meta', '').title(),
                                    "description": "", "type": "form", "sub_type": "config",
                                    "id": hashlib.sha256(
                                        os.path.join(root, name).encode('utf-8')).hexdigest()}}
                    if last_path not in wizard_data:
                        wizard_data.update(wizard_form)
                else:
                    if _dir != last_dir:  # если перешли на новую площадку, то добавляем соответствуюший шаг визарда
                        last_dir = _dir
                        last_path += "/" + _dir
                        wizard_form = {
                            last_path: {"display_name": _dir.title(),
                                        "description": "", "type": "form", "sub_type": "site",
                                        "id": hashlib.sha256(os.path.join(root).encode('utf-8')).hexdigest()}}
                        if last_path not in wizard_data:
                            wizard_data.update(wizard_form)
                    last_path += "/" + name.replace('.yml.meta', '')
                    '''
                    Формирование шага, содержащий данные о конфиге площадки
                    Если конфиг является последним в директории(площадке), то задаем для шага action:deploy
                    '''
                    wizard_group = {
                        last_path: {"display_name": name.replace('.yml.meta', '').title(),
                                    "description": "", "type": "form", "sub_type": "config",
                                    "id": hashlib.sha256(
                                        os.path.join(root, name).encode('utf-8')).hexdigest(),
                                    "action": "deploy" if name == files_in_directory[
                                        -1] and name != "global.yml.meta" else None, "site_name": last_dir}}
                    if last_path not in wizard_data:
                        wizard_data.update(wizard_group)
    last_key, last_value = list(wizard_data.items())[-1]
    last_path = last_key + "/last_step"
    last_form = {
        last_path: {"display_name": "Final stage",
                    "description": "", "type": "form",
                    "id": "final_stage"}}
    if last_path not in wizard_data:
        wizard_data.update(last_form)
    file.close()
    file = open(os.path.join(config.filespath, "wizard.meta"), 'w')
    yaml_config.yaml.dump(wizard_data, file)
    file.close()


'''
Функция для проверки валидности значения параметра
'''


def check_validate_parameter(input_url, value, uid, node):
    parameter = None
    for el in node.elem:
        if input_url in el:
            parameter = el[input_url]
    if parameter:
        try:
            value = check_sub_type_schema_validate(parameter, value, uid, input_url)
            return True, value
        except ValidationError as e:
            return False, str(e)
        except ValueError as e:
            return False, str(e)
    else:
        for key in node.child:
            returned_data = check_validate_parameter(input_url, value, uid, node.child[key]) is not None
            if returned_data is not None:
                return returned_data
        return False, "Parameter not found"


'''
Функция для проверки валидности JSON схемы у параметра
'''


def check_sub_type_schema_validate(parameter, value, uid, input_url):
    if value is None:
        raise ValueError(f"Empty value for parameter with path {input_url}")
    else:
        if parameter.type != "array" and parameter.type != "dict" and str(value).strip() == '':
            raise ValueError(f"Empty value for parameter with path {input_url}")
    if parameter.type == "string":
        value = PlainScalarString(value)
    elif parameter.type == "string-single-quoted":
        value = SingleQuotedScalarString(value)
    elif parameter.type == "string-double-quoted":
        value = DoubleQuotedScalarString(value)
    elem_info = ElemInfo(value=value, type=parameter.type,
                         description=parameter.description,
                         sub_type=parameter.sub_type,
                         sub_type_schema=None,
                         readOnly=parameter.readOnly,
                         additional=parameter.additional,
                         display_name=parameter.display_name,
                         control=parameter.control,
                         constraints=parameter.constraints,
                         file_id=uid)
    if parameter.sub_type_schema is not None:
        for key, metadata in parameter.sub_type_schema.items():
            if isinstance(value, dict):
                if key in value:
                    value[key] = check_sub_type_schema_validate(metadata, value[key], uid, f"{input_url}/{key}")
            elif isinstance(value, list):
                for el in value:
                    if key in el:
                        el[key] = check_sub_type_schema_validate(metadata, el[key], uid, f"{input_url}/{key}")
    return elem_info.value


'''
Функция для формирования дерева форм (навигацинное меню)
'''


def read_ui_file(directory):
    """
        Reads meta file of tree and creates structured tree
    """
    HydraParametersInfo().tree.clear()
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == config.tree_filename:
                with open(os.path.join(root, name), 'r') as stream:
                    data_loaded = yaml_config.yaml.load(stream)
                    for obj in data_loaded:
                        path = obj.split("/")
                        add_node(path, data_loaded[obj]["id"], data_loaded[obj]["type"])
                        add_additional_fields(path, "display_name", data_loaded[obj]["display_name"])
                        if "description" in data_loaded[obj]:
                            add_additional_fields(path, "description", data_loaded[obj]["description"])


'''
Функция для формирования дерева, описывающее шаги визарда
'''


def read_wizard_file(directory):
    """
        Reads meta file of wizard tree and creates structured tree
    """
    HydraParametersInfo().wizard_tree.clear()
    last_id = 0
    for root, dirs, files in os.walk(directory):
        for name in files:
            if name == config.wizard_filename:
                with open(os.path.join(root, name), 'r') as stream:
                    data_loaded = yaml_config.yaml.load(stream)
                    for obj in data_loaded:
                        path = obj.split("/")
                        condition_list = []
                        # if "condition" in data_loaded[obj]:
                        #     condition_data = data_loaded[obj]["condition"]
                        #     for condition in condition_data:
                        #         for key in condition:
                        #             condition_schema = Condition(key=key, allow=condition[key])
                        #             condition_list.append(condition_schema)
                        if last_id != data_loaded[obj]["id"]:
                            last_id == data_loaded[obj]["id"]
                        else:
                            raise ValueError("In file wizard.meta id must be unique")
                        add_node(path, data_loaded[obj]["id"], data_loaded[obj]["type"], condition=condition_list,
                                 # добавление узла дерева
                                 is_wizard=True)
                        '''
                        Добавление дополнительных полей шага визарда
                        '''
                        add_additional_fields(path, "display_name", data_loaded[obj]["display_name"], is_wizard=True)
                        if "description" in data_loaded[obj]:
                            add_additional_fields(path, "description", data_loaded[obj]["description"], is_wizard=True)
                        if "action" in data_loaded[obj]:
                            add_additional_fields(path, "action", data_loaded[obj]["action"], is_wizard=True)
                        if "sub_type" in data_loaded[obj]:
                            add_additional_fields(path, "sub_type", data_loaded[obj]["sub_type"], is_wizard=True)
                        if "site_name" in data_loaded[obj]:
                            add_additional_fields(path, "site_name", data_loaded[obj]["site_name"], is_wizard=True)


'''
Функция генерации данных, описывающих различные архитектуры, и их запись в файл wizard.meta
'''


def generate_wizard_meta(directory):
    file = open(os.path.join(directory, "wizard.meta"), 'r')
    wizard_data = yaml_config.yaml.load(file)
    for root, dirs, files in os.walk(
            os.path.join(config.filespath, "_framework/arch")):  # проход все файлов *meta в папке _framework/arch
        files.sort()
        for name in files:
            if name.endswith("meta"):
                meta_file = open(os.path.join(root, name), 'r')
                meta_file_data = yaml_config.yaml.load(meta_file)
                description = meta_file_data.get("FILE").get("description", "")
                meta_file.close()
                wizard_form = {
                    f"root/{name.replace('.yml.meta', '')}": {"display_name": name.replace('.yml.meta', '').title(),
                                                              "description": description, "type": "group",
                                                              "id": hashlib.sha256(
                                                                  os.path.join(root, name).encode(
                                                                      'utf-8')).hexdigest()}}  # формирование группы для формы root(Каждая группа описывает одну архитектуру)
                if f"root/{name.replace('.yml.meta', '')}" not in wizard_data:
                    wizard_data.update(wizard_form)
    file.close()
    file = open(os.path.join(directory, "wizard.meta"), 'w')
    yaml_config.yaml.dump(wizard_data, file)
    file.close()


'''
Комментирование/Раскомментирование переданного списка элементов
'''


def set_comment_out(content: list[CommentItem]):
    for item in content:
        input_url_list = item.url.split("/")
        key = input_url_list[0]
        if item.is_comment:
            for elements in HydraParametersInfo().get_elements_values():
                if key in elements.values and elements.uid == item.file_id:
                    add_comment_element(elements.values, input_url_list)
                    write_file(elements.values, elements.path, elements.type, item.url)
                    with open(os.path.join(config.filespath, elements.path), 'r') as file:
                        lines = file.readlines()
                        lines_to_keep = [line for line in lines if not line.strip() == "- delete_comment_element"]
                    with open(os.path.join(config.filespath, elements.path), 'w') as file:
                        file.writelines(lines_to_keep)
                    break
        else:
            for elements in HydraParametersInfo().get_elements_values():
                if key in elements.values and elements.uid == item.file_id:
                    remove_comment_element(elements.values, input_url_list, elements.path)
                    break


'''
Функция закомментирования элемента массива
'''


def add_comment_element(values, input_url_list):
    while len(input_url_list) > 1:
        if isinstance(values, dict):
            values = values[input_url_list[0]]
        elif isinstance(values, list):
            values = values[int(input_url_list[0])]
        input_url_list.pop(0)
    values.yaml_set_comment_before_after_key(int(input_url_list[0]), before="head_comment")
    comment, individual_comment = formatted_comment(values[int(input_url_list[0])])
    values.yaml_set_comment_before_after_key(int(input_url_list[0]), before=comment)
    values.yaml_set_comment_before_after_key(int(input_url_list[0]), before="foot_comment")
    if individual_comment is not None and individual_comment != '':
        values.yaml_set_comment_before_after_key(len(values) - 1, before=individual_comment)
    values[int(input_url_list[0])] = "delete_comment_element"


'''
Функция для формиирования закомментированного элемента массива
'''


def formatted_comment(data, indent=0):
    if not (isinstance(data, dict) or isinstance(data, list)):
        if isinstance(data, DoubleQuotedScalarString):
            return f"\"{data}\"", ''
        elif isinstance(data, SingleQuotedScalarString):
            return f"\'{data}\'", ''
        return data, ''
    if isinstance(data, dict):
        comments = []
        comment = ""
        individual_comments = []
        for key in data:
            previous_comment = ''
            # Сохраняем существующий комментарий у объекта
            if hasattr(data, "ca") and key in data.ca.items:
                for ca in data.ca.items[key]:
                    if ca:
                        previous_comment += "\n".join(
                            [line for idx, line in enumerate(ca.value.split("\n")) if line.strip() and idx == 0])
                        individual_comments.append("\n".join(
                            [line.replace("#", "", 1) for idx, line in enumerate(ca.value.split("\n")) if
                             line.strip() and idx > 0]))
            # Создаем комментарий копирующий структуру объекта
            formatted_data = formatted_comment(data[key], indent + 2)
            if comment == "" and indent == 0:
                comment = f"- {key}: {formatted_data[0]} {previous_comment}"
            else:
                comment = f"{' ' * (indent + 2)}{key}: {formatted_data[0]} {previous_comment}"
            comments.append(comment)
            if formatted_data[1].strip() and formatted_data[1].strip() != "" and formatted_data[1].strip() != "\n":
                individual_comments.append(formatted_data[1])
        return "\n".join(comments), "\n".join(individual_comments)
    if isinstance(data, list):
        comments = []
        individual_comments = []
        for index, el in enumerate(data):
            previous_comment = ''
            # Сохраняем существующий комментарий у объекта
            if hasattr(data, "ca") and index in data.ca.items:
                for ca in data.ca.items[index]:
                    if ca:
                        previous_comment += "\n".join(
                            [line for idx, line in enumerate(ca.value.split("\n")) if line.strip() and idx == 0])
                        individual_comments.append("\n".join(
                            [line.replace("#", "", 1) for idx, line in enumerate(ca.value.split("\n")) if
                             line.strip() and idx > 0]))
            # Создаем комментарий копирующий структуру объекта
            formatted_data = formatted_comment(el, indent)
            comments.append(f"\n{' ' * indent}- {formatted_data[0]} {previous_comment}")
            if formatted_data[1].strip() and formatted_data[1].strip() != "" and formatted_data[1].strip() != "\n":
                individual_comments.append(formatted_data[1])
        return "\n".join(comments), "\n".join(individual_comments)


'''
Функция разкомментирования элемента массива
'''


def remove_comment_element(values, input_url_list, path):
    while len(input_url_list) > 1:
        values = values[input_url_list[0]]
        input_url_list.pop(0)
    start_comment_line = values[int(input_url_list[0])].lc.line
    with open(os.path.join(config.filespath, path), 'r') as file:
        lines = file.readlines()
        lines_copy = []
        line_number = 0
        flag = False
        for line in lines:
            line_number += 1
            if line.strip() == "# head_comment" and line_number == start_comment_line:
                flag = True
                continue
            if flag and line.strip() != "# foot_comment" and line.lstrip().startswith("#"):
                line = line.replace("#", " ", 1)
                lines_copy.append(line)
                continue
            if line.strip() == "# foot_comment":
                flag = False
                continue
            lines_copy.append(line)
    with open(os.path.join(config.filespath, path), 'w') as file:
        file.writelines(lines_copy)
