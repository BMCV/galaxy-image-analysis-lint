import pathlib
import unittest
import unittest.mock
import sys

import gialint
from lxml import etree


def _create_check_mock(lines):
    def _check_mock(tool_xml_root, tool_path):
        for line in lines:
            yield line
    return _check_mock


class TestCase(unittest.TestCase):

    code = 'gia000'

    @property
    def module_name(self):
        return f'gialint._checks.{self.code}'

    def setUp(self):
        self.module_mock = unittest.mock.MagicMock()
        sys.modules[self.module_name] = self.module_mock

    def tearDown(self):
        del sys.modules[self.module_name]

    def test(self):
        for suffix in (
            '',
            '<!-- !GIA101 -->',
        ):
            with self.subTest(suffix=suffix):
                xml_test = etree.fromstring(
                    f'''<root>
                        <line2/>
                        <line3/>{suffix}
                        <line4/>
                    </root>'''
                )
                self.module_mock.check = _create_check_mock([3])
                yielded_lines = list(
                    gialint.check(
                        self.code,
                        xml_test,
                        pathlib.Path(),
                    ),
                )
                self.assertEqual(
                    yielded_lines,
                    [3],
                )

    def test_suppressed(self):
        xml_test = etree.fromstring(
            f'''<root>
                <line2/>
                <line3/><!-- !{self.code.upper()} -->
                <line4/>
            </root>'''
        )
        self.module_mock.check = _create_check_mock([3])
        yielded_lines = list(
            gialint.check(
                self.code,
                xml_test,
                pathlib.Path(),
            ),
        )
        self.assertEqual(yielded_lines, list())
