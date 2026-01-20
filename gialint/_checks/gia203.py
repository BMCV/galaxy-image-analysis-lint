import json

from Cheetah import NameMapper
from Cheetah.Template import Template
from Cheetah.Parser import ParseError

from ..utils import (
    get_test_inputs,
    list_tests,
)


def check(tool_xml_root):
    if (inputs_xml_list := tool_xml_root.findall(f'./inputs')):
        inputs_xml = inputs_xml_list[0]
        for test_xml in list_tests(tool_xml_root):
            for template in tool_xml_root.findall(f'./configfiles/configfile'):
                namespace = get_test_inputs(inputs_xml, test_xml)
                try:
                    s = str(Template(template.text, searchList=namespace))
                    try:
                        json.loads(s)
                    except json.JSONDecodeError:
                        yield template.sourceline
                except (ParseError, NameMapper.NotFound):
                    pass  # parse errors are handled by a dedicated check
