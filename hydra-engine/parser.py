import json
import yaml
import os


def parse_meta_params():
    elements = []
    for filename in os.listdir("files"):
        if "meta" in filename:
            with open(os.path.join("files", filename), 'r') as stream:
                data_loaded = yaml.safe_load(stream)
                _elements = data_loaded["PARAMS"]
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
                data_loaded["path"] = file["path"]
                elements.append(data_loaded)
    return elements


elements_yaml = parse_meta_params()
elements_files_info = parse_elements_fileinfo()
elements_json = parse_json()