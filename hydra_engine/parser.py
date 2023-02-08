import json
import uuid
import logging
import yaml
import os

logger = logging.getLogger("common_logger")
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
    elements_yaml.clear()
    for filename in os.listdir("files/config_files"):
        if "meta" in filename:
            with open(os.path.join("files/config_files", filename), 'r') as stream:
                data_loaded = yaml.safe_load(stream)
                _elements = data_loaded["PARAMS"]
                for element in elements_json:
                    for file_info in elements_files_info:
                        if element.path == file_info["path"]:
                            file_info["uid"] = element.uid
            elements_yaml.append(_elements)


def parse_elements_fileinfo():
    elements_files_info.clear()
    for filename in os.listdir("files/config_files"):
        if "meta" in filename:
            if os.path.isfile(os.path.join("files/config_files", filename)):
                with open(os.path.join("files/config_files", filename), 'r') as stream:
                    data_loaded = yaml.safe_load(stream)
                    if data_loaded is not None:
                        _elements = data_loaded["FILE"]
                        elements_files_info.append(_elements)


def parse_value_files():
    elements_json.clear()
    for file in elements_files_info:
        if file["type"] == "json":
            with open(os.path.join("files/config_files", file["path"]), 'r') as stream:
                data_loaded = json.load(stream)
                value_instance = ValuesInstance(file["type"], file["path"], uuid.uuid4().hex, data_loaded)
                elements_json.append(value_instance)
        if file["type"] == "yaml":
            with open(os.path.join("files/config_files", file["path"]), 'r') as stream:
                data_loaded = yaml.safe_load(stream)
                value_instance = ValuesInstance(file["type"], file["path"], uuid.uuid4().hex, data_loaded)
                elements_json.append(value_instance)


def write_file(data, file_path, file_type, key,value):
    try:
        with open(os.path.join("files/config_files", file_path), 'w') as file:
            if file_type == "json":
                file.write(json.dumps(data, sort_keys=False))
            if file_type == "yaml":
                file.write(yaml.safe_dump(data, sort_keys=False))
        logger.info(f"File {file_path} was modified to value {value} in parameter {key}")
    except Exception as e:
        logger.error(f"Error in editing file {file_path} with {e}")


def parse_config_files():
    try:
        parse_elements_fileinfo()
        parse_value_files()
        parse_meta_params()
    except Exception as e:
        logger.error(f"Error in parsing configuration files with {e}")
