import os
from pathlib import Path
import sys
from hydra_engine import config
import yaml
from itertools import chain


def collect_documents_from_raw_files():
    final_documents = []
    key = None
    vals = {}
    total_groups = []
    for path in Path(config.filespath).rglob('*.meta'):
        with open(path, 'r') as stream:
            if path.name == config.tree_filename:  # CONTROLS.META (TREE.META)
                temp_tree_documents = []
                for line in stream.read().split(os.linesep):
                    line = line.strip()
                    if ":" in line:
                        match line.split(":"):
                            case output_url, "":  # key
                                # add to final documents
                                if key:
                                    temp_tree_documents.append({
                                        'output_url': key,
                                        'input_url': "",
                                        'entity': "form",
                                        'description': vals['description'] if 'description' in vals else "",
                                        'display_name': vals['display_name'] if 'display_name' in vals else ""
                                    })
                                key = output_url

                                # not like this probably
                                _index = -1
                                for i, candidate_to_be_refilled in enumerate(total_groups):
                                    if candidate_to_be_refilled in key:  # substring of
                                        _index = i
                                        _key = key
                                        break
                                if _index == -1:
                                    total_groups.append(key)
                                else:
                                    total_groups[_index] = key

                            case name, value:  # parameters names and values
                                vals[name]: value
                for doc in temp_tree_documents:
                    if doc['output_url'] in total_groups:
                        doc['entity'] = 'group'
                final_documents.extend(temp_tree_documents)
            else:
                data_loaded = yaml.safe_load(stream)
                if 'PARAMS' in data_loaded:
                    for params in data_loaded['PARAMS']:
                        for name, values in params.items():
                            final_documents.append({
                                'output_url': values['output_url'] if 'output_url' in values else "",
                                'input_url': name if name else "",
                                'entity': 'field',
                                'description': values['description'] if 'description' in values else "",
                                'display_name': values['render'][
                                    'display_name'] if 'render' in values and 'display_name' in values['render'] else ""
                            })
    return final_documents


def collect_documents_from_fields(fields):
    results = []
    for settings in chain.from_iterable(fields):
        if isinstance(settings, dict):
            for input_url, item in settings.items():
                results.append({
                    'output_url': item['output_url'] if 'output_url' in item else "",
                    'input_url': input_url,
                    'entity': "field",
                    'description': item['description'] if 'description' in item else "",
                    'display_name': item['render']['display_name'] if 'render' in item and 'display_name' in item[
                        'render'] else "",
                })
    return results


def collect_documents_from_tree(tree, pre=""):
    results = []
    if not hasattr(tree, 'child'):
        for key in tree:
            inners = collect_documents_from_tree(tree[key], f"{pre}{key}/")
            results.extend(inners)
    else:
        if len(tree.child) > 0:
            for name in tree.child:
                inners2 = collect_documents_from_tree(tree.child[name], f"{pre}{name}/")
                results.extend(inners2)
            results.append({
                'output_url': pre,
                'input_url': "",
                'entity': "form",
                'description': tree.description if hasattr(tree, 'description') else "",
                'display_name': tree.display_name if hasattr(tree, 'display_name') else "",
            })
        else:
            results.append({
                'output_url': pre,
                'input_url': "",
                'entity': "group",
                'description': tree.description if hasattr(tree, 'description') else "",
                'display_name': tree.display_name if hasattr(tree, 'display_name') else "",
            })

    return results


def get_documents_from_hydra():
    # sys.modules['schemas'].tree костыль ебучий надо выпиливать
    final_documents = []
    tree_docs = collect_documents_from_tree(sys.modules['schemas'].tree)
    settings_docs = collect_documents_from_fields(sys.modules['schemas'].elements_yaml)
    final_documents.extend(tree_docs)
    final_documents.extend(settings_docs)

    return final_documents
