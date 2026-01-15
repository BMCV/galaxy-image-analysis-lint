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


def check(code, tool_xml_root):
    check_name = f'_checks.{code.lower()}'
    check_module = __import__(check_name, globals(), locals(), fromlist=['*'], level=1)
    yield from check_module.check(tool_xml_root)
