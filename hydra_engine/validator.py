import typer
from _app import read_ui_file, parse_config_files
from schemas import ElemInfo

validator = typer.Typer()


@validator.command()
def validate():
    parse_config_files()
    read_ui_file("files")
