from metadata_tool.structure import OEPMetadata


class Parser:
    def parse(self, inp: str) -> OEPMetadata:
        raise NotImplementedError

    def parse_from_file(self, path: str, **kwargs) -> OEPMetadata:
        with open(path, **kwargs) as f:
            return self.parse(''.join(f.readlines()))
