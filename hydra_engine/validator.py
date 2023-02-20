import typer
from schemas import tree

validator = typer.Typer()


@validator.command()
def validate():
    validate_node(tree)
    typer.echo("Hello World")


def validate_node(current_node):
    keys = current_node.keys()
    for key in keys:
        for elem in current_node[key].elem:
            elem[elem.keys()[0]].check_type()
            elem[elem.keys()[0]].check_sub_type()
            elem[elem.keys()[0]].check_control()
            elem[elem.keys()[0]].check_constraints(
            )
        validate_node(current_node[key].child)
