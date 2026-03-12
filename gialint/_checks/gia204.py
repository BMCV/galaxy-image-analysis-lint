import difflib
import pathlib
import re
import textwrap

from Cheetah import NameMapper
from Cheetah.Parser import ParseError
from Cheetah.Template import Template

from ..utils import (
    flat_dict_to_nested,
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


def _list_options(s: str) -> tuple[str, ...]:
    return tuple(
        re.findall(r':([^:]+):', s),
    )


def _apply_options(lines: list[str], options: tuple[str, ...]) -> list[str]:
    result = list()
    for line in lines:

        if 'relax_indent' in options:
            line = line.lstrip()

        if 'relax_linewrap' in options:
            line = line.lstrip().removesuffix('\\')

        if 'relax_whitespace' in options:
            line = re.sub(r' +', ' ', line)

        result.append(line)

    if 'relax_linewrap' in options:
        s = ' '.join(result)
        return (
            [re.sub(r' +', ' ', s)]
            if 'relax_whitespace' in options
            else [s]
        )
    else:
        return result


def check(tool_xml_root, tool_path):
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

            # Strip options that may be given as a suffix
            if ':' in template_id:
                template_id = template_id[:template_id.index(':')].strip()

            # Validate that `template_id` is a valid template
            if template_id not in templates.keys():
                yield dict(
                    line=comment.sourceline,
                    details=f'No such template: "{template_id}"',
                )

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
                    comment_text = (
                        textwrap.dedent(comment.text)
                        .strip()
                        .replace('––', '--')  # double dash is not allowed in XML comments, use double n-dash instead
                    )
                    header = _list_nonempty_lines(comment_text)
                    options = _list_options(header.pop(0)[len(full_prefix):])

                    # Build the template (with the corresponding namespace)
                    namespace = base_namespace | flat_dict_to_nested(get_test_inputs(inputs_xml, test_xml))
                    try:
                        result = str(Template(template.text, searchList=namespace))
                    except (ParseError, NameMapper.NotFound):
                        continue  # Cheetah compile errors are handled by dedicated checks

                    # Validate that `actual` corresponds to `header`
                    actual = _list_nonempty_lines(textwrap.dedent(result))
                    header = _apply_options(header, options)
                    actual = _apply_options(actual, options)
                    if actual != header:
                        yield dict(
                            line=comment.sourceline,
                            details='\n'.join(
                                difflib.unified_diff(
                                    header,
                                    actual,
                                    fromfile='expected',
                                    tofile='actual',
                                    lineterm='',  # avoid extra newlines
                                ),
                            ),
                        )
