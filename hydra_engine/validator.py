import typer
from app import read_controls_file, parse_config_files
from schemas import ElemInfo

validator = typer.Typer()


@validator.command()
def validate():
    parse_config_files()
    read_controls_file("files")
