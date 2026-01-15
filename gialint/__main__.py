import argparse
import pathlib
import sys

from galaxy.util import xml_macros

from . import codes, list_codes, check
from gialint._context import Context


gialint_root_path = pathlib.Path(__file__).parent

parser = argparse.ArgumentParser()
parser.add_argument('--tool_path', required=False, type=str)
args = parser.parse_args()


def list_tool_xml(path):
    if path.is_file():
        yield path
    else:
        for xml_path in path.glob('**/*.xml'):
            yield xml_path


def list_violations(tool_xml_path):
    for code in list_codes():
        for line in check(code, tree.getroot()):
            yield Context(code, getattr(codes, code), tool_xml_path, line)


working_path = pathlib.Path(args.tool_path) or pathlib.Path.cwd()
violations_count = 0
for tool_xml_path in list_tool_xml(working_path):
    tree = xml_macros.load(tool_xml_path)
    if tree.getroot().tag == 'tool':

        sys.stdout.write(f'Linting {tool_xml_path}... ')
        sys.stdout.flush()
        violations = list(list_violations(tool_xml_path))

        if violations:
            print('FAILED')
            for context in violations:
                print(str(context))
        else:
            print('OK')
        violations_count += len(violations)

exit(violations_count)
