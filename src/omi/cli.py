"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -momi` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``omi.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``omi.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import click

from omi.dialects import get_dialect


@click.group()
def grp():
    pass


@grp.command("translate")
@click.option("-f", help="Dialect of the input")
@click.option("-t", default="oep-v1.4", help="Dialect to translate to")
@click.option("-o", default=None, help="Output file")
@click.argument("file_path")
def translate(f, t, o, file_path):
    with open(file_path, "r") as infile:
        from_dialect = get_dialect(f)()
        obj = from_dialect.parse(infile.read())
        to_dialect = get_dialect(t)()
        s = to_dialect.compile_and_render(obj)
        if o:
            with open(o, "w") as outfile:
                outfile.write(s.decode("utf-8"))
        else:
            print(s)


cli = click.CommandCollection(sources=[grp])


def main():
    cli()
