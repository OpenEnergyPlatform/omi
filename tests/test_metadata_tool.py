
from metadata_tool.cli import main


def test_main():
    assert main([]) == 0
