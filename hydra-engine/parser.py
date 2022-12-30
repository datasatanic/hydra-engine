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


def parse_json():
    elements = []
    for file in elements_files_info:
        if file["type"] == "json":
            with open(os.path.join("files", file["path"]), 'r') as stream:
                data_loaded = json.load(stream)
                value_instance = ValuesInstance(file["type"], file["path"], uuid.uuid4().hex, data_loaded)
                elements.append(value_instance)
    return elements


def write_file(json_text, file_path):
    with open(os.path.join("files", file_path), 'w') as file:
        file.write(json.dumps(json_text))


elements_files_info = parse_elements_fileinfo()
elements_json = parse_json()
elements_yaml = parse_meta_params()
