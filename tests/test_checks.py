import pathlib
import unittest
from lxml import etree

import gialint


tests_root_path = pathlib.Path(__file__).parent


def _create_test(code, xml_tests_filepath, xml_test):
    expected_lines_with_violations_str = xml_test.attrib.get('lines_with_volations', '')
    expected_lines_with_violations = (
        [int(line.strip()) for line in expected_lines_with_violations_str.split(',')]
        if expected_lines_with_violations_str.strip() else list()
    )

    def format_lines_list(lines_list):
        return ', '.join(f'{line}' for line in lines_list) or 'none'

    def test(testcase):
        actual_lines_with_violations = list(gialint.check(code, xml_test))
        if actual_lines_with_violations != expected_lines_with_violations:
            testcase.fail(
                f'{xml_tests_filepath}:{xml_test.sourceline}\n'
                f'    expected failures on lines: {format_lines_list(expected_lines_with_violations)}\n'
                f'    but actual failures were on: {format_lines_list(actual_lines_with_violations)}'
            )

    return test


def _create_tests(code):
    xml_tests_filepath = tests_root_path / 'checks' / f'{code}.xml'
    xml_tests = etree.parse(xml_tests_filepath).getroot()
    for xml_test in xml_tests:
        if isinstance(xml_test, etree._Comment):
            continue
        assert xml_test.tag == 'test-tool', xml_test.tag
        yield _create_test(code, xml_tests_filepath, xml_test)


class CodesTestCase(unittest.TestCase):

    pass


for code in gialint.list_codes():
    for test_idx, test in enumerate(_create_tests(code)):
        setattr(CodesTestCase, f'test_{code}_{test_idx + 1}', test)
