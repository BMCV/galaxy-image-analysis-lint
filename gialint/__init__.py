from . import codes
from .version import __version__

__all__ = [
    '__version__',
    'codes',
    'list_codes',
    'check',
]


def list_codes():
    for attr in dir(codes):
        if attr.startswith('GIA'):
            yield attr


def _list_suppressions(code, xml_root):
    xpath = f'.//comment()[normalize-space(.)="!{code.upper()}"]'
    for sup in xml_root.xpath(xpath):
        yield sup.sourceline


def check(code, tool_xml_root, tool_path):
    check_name = f'_checks.{code.lower()}'
    check_module = __import__(check_name, globals(), locals(), fromlist=['*'], level=1)
    suppressions = frozenset(_list_suppressions(code, tool_xml_root))
    for info in check_module.check(
        tool_xml_root,
        tool_path.absolute() if tool_path else None,
    ):
        line = info if isinstance(info, int) else info['line']
        if line not in suppressions:
            yield info
