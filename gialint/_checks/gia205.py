import copy
import difflib
import re
import warnings

from pydantic._internal._generate_schema import (
    UnsupportedFieldAttributeWarning,
)

with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=UnsupportedFieldAttributeWarning)
    warnings.filterwarnings('ignore', category=PendingDeprecationWarning)
    from galaxy.tool_util.parser.xml import XmlToolSource

from lxml import etree


def _guess_required_files_list(command: str) -> list[str]:
    return re.findall(r'\b[\w.-]+\.py\b', command, re.IGNORECASE)


def check(tool_xml_root, tool_path):
    gx_tool_tree = copy.deepcopy(etree.ElementTree(tool_xml_root))
    gx_tool_tree.getroot().tag = 'tool'
    tool = XmlToolSource(gx_tool_tree)

    # Guess required files from the tool command
    if (tool_command := tool.parse_command()):
        expected_required_files_list = list(
            sorted(
                _guess_required_files_list(tool_command),
            ),
        )
    else:
        return

    # Determine list of required files declared in the tool XML
    if (required_files := tool.parse_required_files()):
        required_files_list = list(
            sorted(
                required_files.find_required_files(str(tool_path)),
            ),
        )
    else:
        required_files_list = list()

    if required_files_list != expected_required_files_list:
        yield dict(
            line=tool._command_el.sourceline,
            details='\n'.join(
                difflib.unified_diff(
                    expected_required_files_list,
                    required_files_list,
                    fromfile='expected required_files',
                    tofile='actual required_files',
                    lineterm='',  # avoid extra newlines
                ),
            ),
        )
