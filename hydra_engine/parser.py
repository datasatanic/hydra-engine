import copy

import commentjson as json
import hashlib
import logging
import ruamel.yaml
import os
from datetime import datetime

logger = logging.getLogger("common_logger")
yaml = ruamel.yaml.YAML(typ="rt")


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class HydraParametersInfo(metaclass=SingletonMeta):
    def __init__(self):
        self.tree = {}
        self.wizard_tree = {}
        self.elements_files_info = None
        self.elements_values = None
        self.elements_meta = None
        self.modify_time: datetime

    def get_elements_files_info(self):
        return self.elements_files_info

    def get_elements_values(self):
        return self.elements_values

    def get_elements_metadata(self):
        return self.elements_meta

    def get_tree_structure(self):
        return self.tree

    def get_wizard_tree_structure(self):
        return self.wizard_tree

    def set_modify_time(self):
        self.modify_time = datetime.now()

    def set_lists(self, l1, l2, l3):
        self.elements_files_info = l1
        self.elements_values = l2
        self.elements_meta = l3


base_dir = os.path.dirname(os.path.abspath(__file__))
elements_files_info = []
elements_values = []
elements_meta = []


class ValuesInstance:
    type: str
    path: str
    uid: str
    values: dict = {}

    def __init__(self, _type, _path, _uid, _values):
        self.type = _type
        self.path = _path
        self.uid = _uid
        self.values = _values


def parse_meta_params():
    """
        Parse files with metadata and get info about meta info of different parameters
    """
    elements_meta.clear()
    for root, dirs, files in os.walk(os.path.join(base_dir, "files")):
        for filename in files:
            if "meta" in filename and filename != "ui.meta" and filename != "wizard.meta":
                with open(os.path.join(root, filename), 'r') as stream:
                    data_loaded = yaml.load(stream)
                    _elements = data_loaded["PARAMS"]
                    elements_meta.append(_elements)


def parse_elements_fileinfo():
    """
        Parse files with metadata and get info about configuration files paths and formats
    """
    elements_files_info.clear()
    for root, dirs, files in os.walk(os.path.join(base_dir, "files")):
        for filename in files:
            if "meta" in filename and filename != "ui.meta" and filename != "wizard.meta":
                if os.path.isfile(os.path.join(root, filename)):
                    with open(os.path.join(root, filename), 'r') as stream:
                        data_loaded = yaml.load(stream)
                        if data_loaded is not None:
                            _elements = data_loaded["FILE"]
                            elements_files_info.append(_elements)


def parse_value_files():
    """
        Parse configuration files
    """
    elements_values.clear()
    for file in elements_files_info:
        if not os.path.exists(os.path.join(base_dir, file["path"])):
            d = {}
            with open(os.path.join(base_dir, file["path"]), 'w') as new_file:
                elements = elements_meta[elements_files_info.index(file)]
                for element in elements:
                    for key in element:
                        sub_d = d
                        generate_config_structure(element, key, sub_d)
                if file["type"] == "yaml":
                    yaml.dump(d, new_file)
                elif file["type"] == "json":
                    json.dump(d, new_file, indent=2)
                new_file.close()
        else:
            if file["type"] == "json":
                with open(os.path.join(base_dir, file["path"]), 'r') as stream:
                    data_loaded = json.load(stream)
                    value_instance = ValuesInstance(file["type"], file["path"],
                                                    hashlib.sha256(file["path"].encode('utf-8')).hexdigest(),
                                                    data_loaded)
                    elements_values.append(value_instance)
            if file["type"] == "yaml":
                with open(os.path.join(base_dir, file["path"]), 'r') as stream:
                    data_loaded = yaml.load(stream)
                    value_instance = ValuesInstance(file["type"], file["path"],
                                                    hashlib.sha256(file["path"].encode('utf-8')).hexdigest(),
                                                    data_loaded)
                    elements_values.append(value_instance)
        for element in elements_values:
            if element.path == file["path"]:
                file["uid"] = element.uid


def generate_config_structure(element, key, sub_d):
    if element[key]["type"] == "dict":
        if key in sub_d:
            sub_d = sub_d[key]
        else:
            sub_d.update({key: {}})
            sub_d = sub_d[key]
        if element[key]["sub_type_schema"] is not None:
            for sub_key in element[key]["sub_type_schema"]:
                generate_config_structure(element[key]["sub_type_schema"], sub_key, sub_d)
    else:
        sub_d.update({key: element[key]["default_value"]})


def write_file(data, file_path, file_type, key, value):
    try:
        with open(os.path.join(base_dir, file_path), 'w') as file:
            if file_type == "json":
                json.dump(data, file, indent=2)
            if file_type == "yaml":
                yaml.dump(data, file)
        logger.info(f"File {file_path} was modified to value {value} in parameter {key}")
        file.close()
    except Exception as e:
        logger.error(f"Error in editing file {file_path} with {e}")


def parse_config_files():
    parse_elements_fileinfo()
    parse_meta_params()
    parse_value_files()
    HydraParametersInfo().set_lists(elements_files_info, elements_values, elements_meta)
