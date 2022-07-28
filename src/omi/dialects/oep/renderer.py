import json
from collections import OrderedDict

from omi.dialects.base.renderer import Renderer


class JSONRenderer(json.JSONEncoder, Renderer):
    """
    This enconder sets up a structured oder of the json string when transforming
    it from a python OrderedDict
    """

    def __init__(self, *args, **kwargs):
        super(JSONRenderer, self).__init__(*args, **kwargs)
        self.current_indent = 0
        self.current_indent_str = ""

    def encode(self, o):
        # Special Processing for lists
        if isinstance(o, (list, tuple)):
            primitives_only = True
            for item in o:
                if isinstance(item, (list, tuple, OrderedDict)):
                    primitives_only = False
                    break
            output = []
            if primitives_only:
                for item in o:
                    output.append(json.dumps(item, ensure_ascii=False))
                return "[ " + ", ".join(output) + "  ]"
            else:
                self.current_indent += 2
                self.current_indent_str = "".join(
                    [" " for x in range(self.current_indent)]
                )
                liste = []
                for item in o:
                    output = []
                    # This is performed if in the list is a OrderedDict
                    if isinstance(item, OrderedDict):
                        for key, value in item.items():
                            output.append(json.dumps(key) + ": " + self.encode(value))

                        liste.append(
                            "\n"
                            + 2 * self.current_indent_str
                            + "{"
                            + (",\n" + 2 * self.current_indent_str).join(output)
                            + "}"
                        )

                    else:
                        raise AssertionError(
                            "Only OrderedDicts in lists are properly structured. Please redefine it in the encode function."
                        )
                        output.append(self.current_indent_str + self.encode(item))
                        return "[\n" + ",".join(output) + "]"

                self.current_indent -= 2
                self.current_indent_str = "".join(
                    [" " for x in range(self.current_indent)]
                )

            return "[" + ",".join(liste) + "]"

        elif isinstance(o, OrderedDict):
            output = []
            self.current_indent += 4
            self.current_indent_str = "".join([" " for x in range(self.current_indent)])
            for key, value in o.items():
                output.append(
                    self.current_indent_str
                    + json.dumps(key)
                    + ": "
                    + self.encode(value)
                )
            self.current_indent -= 4
            self.current_indent_str = "".join([" " for x in range(self.current_indent)])
            return "{\n" + ",\n".join(output) + "}"
        else:
            return json.dumps(o, ensure_ascii=False)

    def render(self, inp, *args, **kwargs):
        return self.encode(inp)
