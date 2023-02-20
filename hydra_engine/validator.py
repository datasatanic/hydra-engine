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
            values = elem[list(elem.keys())[0]]
            elem[list(elem.keys())[0]].check_type(values.type, values.__dict__)
            elem[list(elem.keys())[0]].check_sub_type(values.sub_type, values.__dict__)
            elem[list(elem.keys())[0]].check_control(values.control, values.__dict__)
            elem[list(elem.keys())[0]].check_constraints(values.constraints, values.__dict__)
        validate_node(current_node[key].child)
