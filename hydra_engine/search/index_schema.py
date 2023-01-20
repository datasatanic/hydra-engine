from hydra_engine.search.analyzer import multilang_analyzer
from whoosh.fields import TEXT, KEYWORD, SchemaClass, ID, BOOLEAN


class HydraIndexScheme(SchemaClass):
    output_url = ID(stored=True, unique=True)
    input_url = KEYWORD(stored=True)
    hitable = BOOLEAN()
    display_name = KEYWORD(stored=True, lowercase=True, field_boost=3.0, scorable=False)
    description = TEXT(analyzer=multilang_analyzer, spelling=True, stored=True)

    def __new__(cls):
        obj = super().__new__(cls)
        obj.showable_fields = ['output_url', 'display_name', 'description']
        return obj
