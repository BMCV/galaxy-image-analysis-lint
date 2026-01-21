import pathlib
import unittest
from lxml import etree

from gialint import utils


tools_root_path = pathlib.Path(__file__).parent / 'tools'


class ToolTest(unittest.TestCase):

    tool: str

    def setUp(self):
        self.tool_xml_root = etree.parse(tools_root_path / self.tool).getroot()
        if (inputs := self.tool_xml_root.findall('./inputs')):
            self.inputs_xml = inputs[0]
        else:
            self.inputs_xml = None
        self.test_xml_list = self.tool_xml_root.findall('./tests/test')


class MinimalTest(ToolTest):

    tool = 'utils_minimal.xml'

    def test_list_tests(self):
        self.assertEqual(len(list(utils.list_tests(self.tool_xml_root))), 1)


class IllegalTest(ToolTest):

    tool = 'utils_illegal.xml'

    def test_list_tests(self):
        self.assertEqual(len(list(utils.list_tests(self.tool_xml_root))), 1)

    def test_get_test_inputs1(self):
        test_inputs = (
            utils.get_test_inputs(self.inputs_xml, self.test_xml_list[0])
        )
        self.assertEqual(test_inputs, dict())


class FullTest(ToolTest):

    tool = 'utils_full.xml'

    def test_list_tests(self):
        self.assertEqual(len(list(utils.list_tests(self.tool_xml_root))), 2)

    def test_get_test_inputs1(self):
        test_inputs = (
            utils.get_test_inputs(self.inputs_xml, self.test_xml_list[0])
        )

        # Validate input parameters without default values
        for key in (
            'text',
            'integer',
            'float',
            'color',
            'hidden',
        ):
            self.assertIsNone(test_inputs[f'{key}_without_default'], None)

        # Validate input parameters with default values
        self.assertEqual(test_inputs['text_with_default'], 'default')
        self.assertEqual(test_inputs['integer_with_default'], 1)
        self.assertEqual(test_inputs['float_with_default'], 1.0)
        self.assertEqual(test_inputs['boolean_1'], 'true')
        self.assertEqual(test_inputs['boolean_2'], 'FALSE')
        self.assertEqual(test_inputs['color_with_default'], '#ff0000')
        self.assertEqual(test_inputs['hidden_with_default'], 'default')
        self.assertEqual(test_inputs['select_1'], 'default')

        # Validate conditionals
        self.assertEqual(test_inputs['cond.text_1'], 'value_1')
        self.assertEqual(test_inputs['cond.text_2'], 'value_2')
        self.assertNotIn('cond.text_0', test_inputs)

    def test_get_test_inputs2(self):
        test_inputs = (
            utils.get_test_inputs(self.inputs_xml, self.test_xml_list[1])
        )

        self.assertEqual(test_inputs['text_with_default'], 'override')
        self.assertEqual(test_inputs['text_without_default'], 'override')
        self.assertEqual(test_inputs['integer_with_default'], 2)
        self.assertEqual(test_inputs['integer_without_default'], 2)
        self.assertEqual(test_inputs['float_with_default'], 2.0)
        self.assertEqual(test_inputs['float_without_default'], 2.0)
        self.assertEqual(test_inputs['boolean_1'], 'false')
        self.assertEqual(test_inputs['boolean_2'], 'TRUE')
        self.assertEqual(test_inputs['color_with_default'], '#00ff00')
        self.assertEqual(test_inputs['color_without_default'], '#00ff00')
        self.assertEqual(test_inputs['hidden_with_default'], 'override')
        self.assertEqual(test_inputs['hidden_without_default'], 'override')
        self.assertEqual(test_inputs['select_1'], 'other')

        # Validate conditionals
        self.assertEqual(test_inputs['cond.text_0'], 'override')
        self.assertEqual(test_inputs['cond.text_1'], 'value_3')
        self.assertNotIn('cond.text_2', test_inputs)
