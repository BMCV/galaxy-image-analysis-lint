import argparse
import pathlib
import sys

from galaxy.util import xml_macros

import yaml

from . import (
    check,
    codes,
    list_codes,
)
from ._context import Context

# Monkey-patch `xml_macros` to not remove comments:
xml_macros.raw_xml_tree = lambda path: (
    xml_macros.parse_xml(path, strip_whitespace=False, remove_comments=False)
)

gialint_root_path = pathlib.Path(__file__).parent

parser = argparse.ArgumentParser()
parser.add_argument('--tool_path', required=False, type=str)
parser.add_argument('--ignore', action='append', type=str, default=list())
parser.add_argument('--details_indent', type=int, default=4)
parser.add_argument('--config', type=str, default='.gialint.yml')
args = parser.parse_args()

if args.config:
    with open(args.config, 'r') as fp:
        config = yaml.safe_load(fp)
else:
    config = dict()


def list_tool_xml(path):
    if path.is_file():
        yield path
    else:
        for xml_path in path.glob('**/*.xml'):
            yield xml_path


def list_violations(tool_xml_path, ignore_codes):
    for code in list_codes():

        # Skip the check if it was passed via `--ignore`
        if code in ignore_codes:
            continue

        # Skip the check if it was listed in the `--config` file
        skip = False
        for pattern, c in config.items():
            if pathlib.Path(tool_xml_path).match(pattern) and (
                code in filter(lambda s: s.strip(), c.get('ignore', list()))
            ):
                skip = True
                break
        if skip:
            continue

        # Run the checks
        for info in check(code, tree.getroot()):
            if isinstance(info, int):
                info = dict(line=info)
            yield Context(code, getattr(codes, code), tool_xml_path, **info)


working_path = pathlib.Path(args.tool_path) or pathlib.Path.cwd()
violations_count = 0
for tool_xml_path in list_tool_xml(working_path):
    tree = xml_macros.load(tool_xml_path)
    if tree.getroot().tag == 'tool':

        sys.stdout.write(f'Linting {tool_xml_path}... ')
        sys.stdout.flush()
        violations = list(list_violations(tool_xml_path, args.ignore))

        if violations:
            print('FAILED')
            print()
            for context in violations:
                print(str(context), file=sys.stderr)
                if context.details:
                    print(
                        '\n'.join(
                            (
                                ' ' * args.details_indent + line
                                for line in str(context.details).splitlines()
                            ),
                        ),
                        file=sys.stderr,
                    )
            print()
        else:
            print('OK')
        violations_count += len(violations)

exit(violations_count)
