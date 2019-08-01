import click
import get_wheel_symbols
import get_sys_symbols
import pypi_tests
from pprint import PrettyPrinter

pp = PrettyPrinter(indent=4)

@click.group()
def cli():
    pass

@cli.command("wheel-syms")
@click.option("--wheel", "-w", required=True)
def get_wheel_syms(wheel):
    result = get_wheel_symbols.get_versioned_symbols_from_whl(wheel)
    pp.pprint(result)

@cli.command("system-syms")
def get_sys_syms():
    result = get_sys_symbols.get_system_symbols()
    pp.pprint(result)

@cli.command("top-pypi")
@click.option("--n", "-n", required=False, type=int)
def get_pypi_symbols(n=100):
    result = dict()
    pypi_tests.get_top_package_symbols(result, n)
    pp.pprint(result)

if __name__=="__main__":
    cli()
