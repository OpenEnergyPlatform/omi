import click
from click.testing import CliRunner
from omi.cli import translate
import json

def test_cli_translation():
    @click.command()
    @click.argument('name')
    def hello(name):
        click.echo('Hello %s!' % name)

    runner = CliRunner()
    result = runner.invoke(translate, ["-f", "oep-v1.3", "-t", "oep-v1.4", "tests/data/metadata_v13.json"])
    with open("tests/data/metadata_v13_converted.json") as expected_file:
        expected = json.loads(expected_file.read())
        assert result.exit_code == 0
        assert json.loads(result.output) == expected
