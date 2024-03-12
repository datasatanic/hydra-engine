import copy
import commentjson as json
import hashlib
import logging
import ruamel.yaml
import os
from datetime import datetime
from hydra_engine.configs import config

logger = logging.getLogger("common_logger")
yaml = ruamel.yaml.YAML(typ="rt")


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class WizardInfo(metaclass=SingletonMeta):
    def __init__(self):
        self.wizard_state: WizardState = None

    def update_current_step(self, url: str):
        self.wizard_state.current_step = url

    def update_arch_name(self, name: str):
        self.wizard_state.arch.arch_name = name

    def update_arch_status(self, status: str):
        self.wizard_state.arch.status = status

    def get_sites_info(self):
        return self.wizard_state.sites

    def get_current_arch_name(self):
        return self.wizard_state.arch.arch_name

    def add_site(self, site):
        self.wizard_state.sites.append(site)

    def remove_site(self, site):
        self.wizard_state.sites.remove(site)


class HydraParametersInfo(metaclass=SingletonMeta):
    def __init__(self):
        self.tree = {}
        self.wizard_tree = {}
        self.elements_files_info = None
        self.elements_values = None
        self.elements_meta = None
        self.was_modified: bool = False
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
    for root, dirs, files in os.walk(config.filespath):
        files.sort()
        if "_framework" and "arch" in root or "_framework" not in root:
            for filename in files:
                if "meta" in filename and filename != config.tree_filename and filename != config.wizard_filename:
                    with open(os.path.join(root, filename), 'r') as stream:
                        data_loaded = yaml.load(stream)
                        if data_loaded is not None and "PARAMS" in data_loaded:
                            _elements = data_loaded["PARAMS"]
                            elements_meta.append(_elements)


def parse_elements_fileinfo():
    """
        Parse files with metadata and get info about configuration files paths and formats
    """
    elements_files_info.clear()
    for root, dirs, files in os.walk(config.filespath):
        files.sort()
        if "_framework" and "arch" in root or "_framework" not in root:
            for filename in files:
                if "meta" in filename and filename != config.tree_filename and filename != config.wizard_filename:
                    if os.path.isfile(os.path.join(root, filename)):
                        with open(os.path.join(root, filename), 'r') as stream:
                            data_loaded = yaml.load(stream)
                            if data_loaded is not None:
                                if "FILE" in data_loaded:
                                    data_loaded["FILE"]["path"] = os.path.join(root, data_loaded["FILE"]["path"])
                                    _elements = data_loaded["FILE"]
                                    _elements["uid"] = hashlib.sha256(
                                        os.path.join(root, filename).encode('utf-8')).hexdigest()
                                    _elements["meta_path"] = os.path.join(root, filename)
                                    elements_files_info.append(_elements)


def parse_value_files():
    """
        Parse configuration files
    """
    elements_values.clear()
    for file in elements_files_info:
        if file["type"] == "json":
            with open(os.path.join(config.filespath, file["path"]), 'r') as stream:
                data_loaded = json.load(stream)
                value_instance = ValuesInstance(file["type"], file["path"],
                                                file["uid"],
                                                data_loaded)
                elements_values.append(value_instance)
        if file["type"] == "yaml":
            with open(os.path.join(config.filespath, file["path"]), 'r') as stream:
                data_loaded = yaml.load(stream)
                value_instance = ValuesInstance(file["type"], file["path"],
                                                file["uid"],
                                                data_loaded)
                elements_values.append(value_instance)


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
        input_url_list = key.split("/")
        while len(input_url_list) > 1:
            sub_d.update({input_url_list[0]: {}})
            sub_d = sub_d[input_url_list[0]]
            input_url_list.pop(0)
        sub_d.update({input_url_list[0]: element[key]["default_value"]})


def write_file(data, file_path, file_type, key, value=None):
    try:
        with open(os.path.join(config.filespath, file_path), 'w') as file:
            if file_type == "json":
                json.dump(data, file, indent=2)
            if file_type == "yaml":
                yaml.dump(data, file)
        if value:
            logger.info(f"File {file_path} was modified to value {value} in parameter {key}")
        file.close()
    except Exception as e:
        logger.error(f"Error in editing file {file_path} with {e}")


def parse_config_files():
    parse_elements_fileinfo()
    parse_meta_params()
    parse_value_files()
    HydraParametersInfo().set_lists(elements_files_info, elements_values, elements_meta)


def read_hydra_ignore():
    ignore_dirs = []
    ignore_extension = []
    file = open(os.path.join(base_dir, ".hydraignore"), 'r')
    for line in file:
        current_line = line.rstrip('\n')
        if current_line.endswith("/"):
            ignore_dirs.append(current_line[:-1])
        elif current_line.startswith("*."):
            ignore_extension.append(current_line[2:])
    file.close()
    return ignore_dirs, ignore_extension
