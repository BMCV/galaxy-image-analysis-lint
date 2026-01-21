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
    for path in (
        'command',
        'configfiles/configfile',
    ):
        for template in tool_xml_root.findall(f'./{path}'):

            # Test build the template
            try:
                Template(template.text, searchList=dict())
            except ParseError as error:
                yield dict(
                    line=template.sourceline,
                    details=error,
                )
                continue

            # Build the template for each test (with the corresponding namespace)
            if (inputs_xml_list := tool_xml_root.findall(f'./inputs')):
                inputs_xml = inputs_xml_list[0]
                for test_num, test_xml in enumerate(list_tests(tool_xml_root), start=1):
                    namespace = base_namespace | flat_dict_to_nested(get_test_inputs(inputs_xml, test_xml))
                    try:
                        str(Template(template.text, searchList=namespace))
                    except (
                        NameMapper.NotFound,
                        TypeError,
                    ) as error:
                        yield dict(
                            line=template.sourceline,
                            details=f'{error} from test {test_num} (line {test_xml.sourceline})',
                        )
