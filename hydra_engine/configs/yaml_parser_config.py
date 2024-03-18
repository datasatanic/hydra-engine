import ruamel.yaml
from ruamel.yaml.comments import CommentedMap, CommentedSeq, CommentedKeySeq
import logging

logger = logging.getLogger("common_logger")


class YamlParserConfig:
    def __init__(self):
        self.yaml = ruamel.yaml.YAML(typ='rt')
