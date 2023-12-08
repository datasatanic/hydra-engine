import commentjson as json
import hashlib
import logging
import ruamel.yaml
import os

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
        self.elements_files_info = None
        self.elements_values = None
        self.elements_meta = None

    def get_elements_files_info(self):
        return self.elements_files_info

    def get_elements_values(self):
        return self.elements_values

    def get_elements_metadata(self):
        return self.elements_meta

    def get_tree_structure(self):
        return self.tree

    def set_lists(self, l1, l2, l3):
        self.elements_files_info = l1
        self.elements_values = l2
        self.elements_meta = l3


base_dir = os.path.dirname(os.path.abspath(__file__))
elements_files_info = []
elements_json = []
elements_yaml = []


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
    elements_yaml.clear()
    ui_meta_data = {}
    with open(os.path.join(base_dir, "files/ui.meta"), 'r') as stream:
        data = yaml.load(stream)
        for key in data:
            ui_meta_data[data[key]["id"]] = key
    for root, dirs, files in os.walk(os.path.join(base_dir, "files")):
        for filename in files:
            if "meta" in filename and filename != "ui.meta":
                with open(os.path.join(root, filename), 'r') as stream:
                    data_loaded = yaml.load(stream)
                    _elements = data_loaded["PARAMS"]
                    for el in _elements:
                        for key in el:
                            if el[key]["id"] in ui_meta_data:
                                el[key]["output_url"] = ui_meta_data[el[key]["id"]]
                    for element in elements_json:
                        for file_info in elements_files_info:
                            if element.path == file_info["path"]:
                                file_info["uid"] = element.uid
                    elements_yaml.append(_elements)


def parse_elements_fileinfo():
    """
        Parse files with metadata and get info about configuration files paths and formats
    """
    elements_files_info.clear()
    for root, dirs, files in os.walk(os.path.join(base_dir, "files")):
        for filename in files:
            if "meta" in filename and filename != "ui.meta":
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
    elements_json.clear()
    for file in elements_files_info:
        if file["type"] == "json":
            with open(os.path.join(base_dir, file["path"]), 'r') as stream:
                data_loaded = json.load(stream)
                value_instance = ValuesInstance(file["type"], file["path"],
                                                hashlib.sha256(file["path"].encode('utf-8')).hexdigest(),
                                                data_loaded)
                elements_json.append(value_instance)
        if file["type"] == "yaml":
            with open(os.path.join(base_dir, file["path"]), 'r') as stream:
                data_loaded = yaml.load(stream)
                value_instance = ValuesInstance(file["type"], file["path"],
                                                hashlib.sha256(file["path"].encode('utf-8')).hexdigest(),
                                                data_loaded)
                elements_json.append(value_instance)


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
    parse_value_files()
    parse_meta_params()
    HydraParametersInfo().set_lists(elements_files_info, elements_json, elements_yaml)
