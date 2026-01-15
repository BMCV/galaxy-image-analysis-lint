import argparse
import pathlib
import sys
from xml.etree import ElementTree

from galaxy.util import xml_macros

from gialint import codes
from gialint.errors import LintError


gialint_root_path = pathlib.Path(__file__).parent

parser = argparse.ArgumentParser()
parser.add_argument('--tool_path', required=False, type=str)
args = parser.parse_args()

working_path = pathlib.Path(args.tool_path) or pathlib.Path.cwd()
tool_xml_path = working_path

tree = xml_macros.load(tool_xml_path)

def list_codes():
    for attr in dir(codes):
        if attr.startswith('GIA'):
            yield attr

def list_violations():
    for code in list_codes():
        check_name = f'_checks.{code.lower()}'
        check_module = __import__(check_name, globals(), locals(), fromlist=['*'], level=1)
        error = LintError(code, getattr(codes, code), tool_xml_path, line=None)
        try:
            check_module.check(tree, error)
        except LintError as error:
            yield error

violations_count = 0
for error in list_violations():
    print(str(error))
    violations_count += 1

exit(violations_count)
