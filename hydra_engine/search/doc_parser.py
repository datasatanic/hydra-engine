import os
from pathlib import Path
from hydra_engine import config
import yaml


def get_documents_from_hydra():
    final_documents = []
    key = None
    vals = {}
    for path in Path(config.filespath).rglob('*.meta'):
        with open(path, 'r') as stream:
            if path.name == config.tree_filename:
                for line in stream.read().split(os.linesep):
                    line = line.strip()
                    if ":" in line:
                        match line.split(":"):
                            case output_url, "":  # key
                                # add to final documents
                                if key:
                                    final_documents.append({
                                        'output_url': key,
                                        'input_url': "",
                                        'description': vals['description'] if 'description' in vals else "",
                                        'display_name': vals['display_name'] if 'display_name' in vals else ""
                                    })
                                key = output_url
                            case name, value:  # parameters names and values
                                vals[name]: value
            else:
                data_loaded = yaml.safe_load(stream)
                if 'PARAMS' in data_loaded:
                    for params in data_loaded['PARAMS']:
                        for name, values in params.items():
                            final_documents.append({
                                'output_url': values['output_url'] if 'output_url' in values else "",
                                'input_url': name if name else "",
                                'description': values['description'] if 'description' in values else "",
                                'display_name': values['render'][
                                    'display_name'] if 'render' in values and 'display_name' in values['render'] else ""
                            })
    return final_documents
