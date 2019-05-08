"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mmetadata_tool` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``metadata_tool.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``metadata_tool.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import sys
import os
from metadata_tool import metadata_version_to_1_4
from metadata_tool import metadata_rdfttl
import click

@click.command()
def translate():
    pass

cli = click.CommandCollection(sources=[translate])

def main(argv=sys.argv):
    """
    Args:
        argv (list): List of arguments

    Returns:
        int: A return code

    Does stuff.
    """
    print(argv)

    if(len(argv) < 2):
        print("usage: ")
        exit()
    path = sys.argv[1]
    filename, file_extension = os.path.splitext(path)
    outputfile = filename + "_converted" + file_extension
    if(len(sys.argv) >= 3):
        outputfile = sys.argv[2]
    try:
        with open(path, "r") as read_file:
            print("Converting " + read_file.name + " ...")
            if(file_extension == '.json'):
                metadata_version_to_1_4.metadata_conversion(path, outputfile, "converter_script", "")
                metadata_rdfttl.jsonToTtl(read_file)
            else:
                print("json file please")
    except Exception as e:
        print(e)
    print("Done")

    return 0
