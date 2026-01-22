import json
import textwrap

from Cheetah import NameMapper
from Cheetah.Template import Template
from Cheetah.Parser import ParseError

from ..utils import (
    flat_dict_to_nested,
    get_base_namespace,
    get_test_inputs,
    list_tests,
)


def check(tool_xml_root):
    base_namespace = get_base_namespace(tool_xml_root)
    if (inputs_xml_list := tool_xml_root.findall(f'./inputs')):
        inputs_xml = inputs_xml_list[0]
        for test_num, test_xml in enumerate(list_tests(tool_xml_root), start=1):
            for template in tool_xml_root.findall(f'./configfiles/configfile'):
                namespace = base_namespace | flat_dict_to_nested(get_test_inputs(inputs_xml, test_xml))
                try:
                    s = str(Template(template.text, searchList=namespace))
                    try:
                        json.loads(s)
                    except json.JSONDecodeError:
                        yield dict(
                            line=template.sourceline,
                            details=(
                                f'from test {test_num} (line {test_xml.sourceline}):\n' +
                                textwrap.dedent(s).strip()
                            ),
                        )
                except (ParseError, NameMapper.NotFound):
                    pass  # parse errors are handled by a dedicated check
