import ruamel.yaml


class YamlParserConfig:
    def __init__(self):
        self.yaml = ruamel.yaml.YAML(typ='rt')
