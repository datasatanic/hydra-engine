import json
import uuid

import yaml
import os


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
    elements = []
    for filename in os.listdir("files"):
        if "meta" in filename:
            with open(os.path.join("files", filename), 'r') as stream:
                data_loaded = yaml.safe_load(stream)
                _elements = data_loaded["PARAMS"]
                for element in elements_json:
                    for file_info in elements_files_info:
                        if element.path == file_info["path"]:
                            file_info["uid"] = element.uid
            elements.append(_elements)
    return elements


def parse_elements_fileinfo():
    elements = []
    for filename in os.listdir("files"):
        if "meta" in filename:
            with open(os.path.join("files", filename), 'r') as stream:
                data_loaded = yaml.safe_load(stream)
                _elements = data_loaded["FILE"]
                elements.append(_elements)
    return elements


def parse_value_files():
    elements = []
    for file in elements_files_info:
        if file["type"] == "json":
            with open(os.path.join("files", file["path"]), 'r') as stream:
                data_loaded = json.load(stream)
                value_instance = ValuesInstance(file["type"], file["path"], uuid.uuid4().hex, data_loaded)
                elements.append(value_instance)
        if file["type"] == "yaml":
            with open(os.path.join("files", file["path"]), 'r') as stream:
                data_loaded = yaml.safe_load(stream)
                value_instance = ValuesInstance(file["type"], file["path"], uuid.uuid4().hex, data_loaded)
                elements.append(value_instance)
    return elements


def write_file(data, file_path, file_type):
    with open(os.path.join("files", file_path), 'w') as file:
        if file_type == "json":
            file.write(json.dumps(data, sort_keys=False))
        if file_type == "yaml":
            file.write(yaml.safe_dump(data, sort_keys=False))


elements_files_info = parse_elements_fileinfo()
elements_json = parse_value_files()
elements_yaml = parse_meta_params()
