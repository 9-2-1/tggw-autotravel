import rich

import tggwpy.plugin as plugin
import tggwpy.plugins.neriview as neriview


def parse_file_to_screen(filename: str) -> plugin.Screen:
    with open(filename, "r", encoding="utf-8") as file:
        content = file.read()
        return plugin.Screen.parse(content)


test_screen = parse_file_to_screen("neritest/underground1.txt")
rich.inspect(neriview.NeriView.parse_screen(test_screen))

test_screen = parse_file_to_screen("neritest/dead_minus.txt")
rich.inspect(neriview.NeriView.parse_screen(test_screen))
