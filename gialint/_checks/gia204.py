import textwrap
import pathlib

from Cheetah import NameMapper
from Cheetah.Template import Template
from Cheetah.Parser import ParseError
from lxml import etree

from ..utils import (
    get_base_namespace,
    get_test_inputs,
    list_tests,
)

prefix = pathlib.Path(__file__).stem.upper() + ':'  # GIA204:


def _xpath_or_none(root, xpath: str):
    if (result := root.xpath(xpath)):
        return result[0]
    else:
        return None


def _list_nonempty_lines(s: str) -> list[str]:
    return list(
        filter(
            lambda line: len(line.strip()) > 0,
            s.splitlines(),
        ),
    )


def check(tool_xml_root):
    templates = {
        template.attrib.get('name', ''): template
        for template in tool_xml_root.xpath('./command | ./configfiles/configfile')
    }

    # Validate that annotations correspond to valid templates
    for test_xml in list_tests(tool_xml_root):
        for comment in test_xml.xpath(
            f'./comment()[starts-with(normalize-space(.), "{prefix}")]',
        ):
            comment_text = textwrap.dedent(comment.text).strip()
            header = _list_nonempty_lines(comment_text)

            # Do not strip this, because the `xpath` lookup below requires the original tokens:
            template_id = header.pop(0).removeprefix(prefix).removeprefix(' ')

            # Validate that `template_id` is a valid template
            if template_id not in templates.keys():
                yield comment.sourceline

    # Build and validate the template for each test (with the corresponding namespace)
    base_namespace = get_base_namespace(tool_xml_root)
    for template_id, template in templates.items():

        # Find tests that have templates defined for the check
        if (inputs_xml_list := tool_xml_root.findall(f'./inputs')):
            inputs_xml = inputs_xml_list[0]
            for test_xml in list_tests(tool_xml_root):
                full_prefix = f'{prefix} {template_id}' if template_id else prefix
                if (
                    comment := _xpath_or_none(
                        test_xml,
                        f'./comment()[starts-with(normalize-space(.), "{full_prefix}")]',
                    )
                ) is not None:
                    comment_text = textwrap.dedent(comment.text).strip()
                    header = _list_nonempty_lines(comment_text)
                    header.pop(0)

                    # Build the template (with the corresponding namespace)
                    namespace = base_namespace | get_test_inputs(inputs_xml, test_xml)
                    try:
                        result = str(Template(template.text, searchList=namespace))
                    except (ParseError, NameMapper.NotFound):
                        continue  # Cheetah compile errors are handled by dedicated checks

                    # Validate that `actual` corresponds to `header`
                    actual = _list_nonempty_lines(textwrap.dedent(result))
                    if actual != header:
                        print(actual)
                        yield comment.sourceline
