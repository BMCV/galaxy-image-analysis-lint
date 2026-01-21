from Cheetah import NameMapper
from Cheetah.Template import Template
from Cheetah.Parser import ParseError

from ..utils import (
    get_test_inputs,
    list_tests,
)


def _get_base_namespace(tool_xml_root):
    ns = dict()
    for configfile in tool_xml_root.findall('./configfiles/configfile'):
        if (name := configfile.attrib.get('name')):
            ns[name] = name
    return ns


def check(tool_xml_root):
    base_namespace = _get_base_namespace(tool_xml_root)
    for path in (
        'command',
        'configfiles/configfile',
    ):
        for template in tool_xml_root.findall(f'./{path}'):

            # Test build the template
            try:
                Template(template.text, searchList=dict())
            except ParseError:
                yield template.sourceline
                continue

            # Build the template for each test (with the corresponding namespace)
            if (inputs_xml_list := tool_xml_root.findall(f'./inputs')):
                inputs_xml = inputs_xml_list[0]
                for test_xml in list_tests(tool_xml_root):
                    namespace = base_namespace | get_test_inputs(inputs_xml, test_xml)
                    try:
                        str(Template(template.text, searchList=namespace))
                    except NameMapper.NotFound:
                        yield template.sourceline
