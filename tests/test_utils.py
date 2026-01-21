import pathlib
import unittest
from lxml import etree

from gialint import utils


tools_root_path = pathlib.Path(__file__).parent / 'tools'


class flat_dict_to_nested(unittest.TestCase):

    def test(self):
        flat = {
            'root.key1': '1',
            'root.key2': '2',
            'root.sub1.key1': '1.1',
            'root.sub1.key2': '1.2',
            'root.list': [
                {
                    'key1': 'a',
                    'key2': 'b',
                },
                {
                    'list_item_root.key1': 'c',
                    'list_item_root.key2': 'd',
                },
            ],
        }
        self.assertEqual(
            utils.flat_dict_to_nested(flat),
            {
                'root': {
                    'key1': '1',
                    'key2': '2',
                    'sub1': {
                        'key1': '1.1',
                        'key2': '1.2',
                    },
                    'list': [
                        {
                            'key1': 'a',
                            'key2': 'b',
                        },
                        {
                            'list_item_root': {
                                'key1': 'c',
                                'key2': 'd',
                            },
                        },
                    ]
                },
            },
        )


class InputDataset(unittest.TestCase):

    def setUp(self):
        self.filepath = '/path/filename.ext1.ext2'
        self.dataset = utils.InputDataset(self.filepath)

    def test_ext(self):
        self.assertEqual(self.dataset.ext(), 'ext1.ext2')

    def test_extension(self):
        self.assertEqual(self.dataset.extension(), 'ext1.ext2')

    def test__str__(self):
        self.assertEqual(str(self.dataset), self.filepath)

    def test_name(self):
        self.assertEqual(self.dataset.name(), 'filename.ext1.ext2')

    def test_id(self):
        self.assertEqual(self.dataset.id(), str(hash(self.filepath)))

    def test_element_identifier(self):
        self.assertEqual(self.dataset.element_identifier(), str(hash(self.filepath)))

    def test_extra_files_path(self):
        self.assertEqual(self.dataset.extra_files_path(), self.filepath)

    def test_metadata(self):
        self.assertFalse(hasattr(self.dataset.metadata(), 'store_root'))
        self.assertEqual(
            utils.InputDataset('filename.zarr').metadata().store_root(),
            'store_root',
        )


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
        self.assertEqual(test_inputs['section_1.no_name'], 'false')
        for key in (
            'text_without_default',
            'integer_without_default',
            'float_without_default',
            'color_without_default',
            'hidden_without_default',
            'section_1.text_without_default',
        ):
            self.assertIsNone(test_inputs[key], None)

        # Validate input parameters with default values
        self.assertEqual(test_inputs['text_with_default'], 'default')
        self.assertEqual(test_inputs['integer_with_default'], '1')
        self.assertEqual(test_inputs['float_with_default'], '1')
        self.assertEqual(test_inputs['boolean_1'], 'true')
        self.assertEqual(test_inputs['boolean_2'], 'FALSE')
        self.assertEqual(test_inputs['color_with_default'], '#ff0000')
        self.assertEqual(test_inputs['hidden_with_default'], 'default')
        self.assertEqual(test_inputs['select_1'], 'default')
        self.assertEqual(test_inputs['select_2'], 'default')
        self.assertEqual(test_inputs['section_1.text_with_default'], 'section_default')
        self.assertNotIn('section_1', test_inputs)

        # Validate conditionals
        self.assertEqual(test_inputs['cond.text_1'], 'value_1')
        self.assertEqual(test_inputs['cond.text_2'], 'value_2')
        self.assertNotIn('cond', test_inputs)
        self.assertNotIn('cond.text_0', test_inputs)

        # Validate repeats
        self.assertEqual(
            test_inputs['repeat_1'],
            [
                dict(repeat_integer_with_default='1', repeat_integer_without_default=None),
                dict(repeat_integer_with_default='2', repeat_integer_without_default=None),
            ],
        )
        self.assertEqual(
            test_inputs['repeat_2'],
            [
                dict(repeat_integer_with_default='3', repeat_integer_without_default=None),
            ],
        )
        self.assertEqual(
            [
                key for key in test_inputs
                if key.startswith('repeat_')
            ],
            [
                'repeat_1',
                'repeat_2',
            ],
        )

    def test_get_test_inputs2(self):
        test_inputs = (
            utils.get_test_inputs(self.inputs_xml, self.test_xml_list[1])
        )

        self.assertEqual(test_inputs['text_with_default'], 'override')
        self.assertEqual(test_inputs['text_without_default'], 'override')
        self.assertEqual(test_inputs['integer_with_default'], '2')
        self.assertEqual(test_inputs['integer_without_default'], '2')
        self.assertEqual(test_inputs['float_with_default'], '2')
        self.assertEqual(test_inputs['float_without_default'], '2')
        self.assertEqual(test_inputs['boolean_1'], 'false')
        self.assertEqual(test_inputs['boolean_2'], 'TRUE')
        self.assertEqual(test_inputs['color_with_default'], '#00ff00')
        self.assertEqual(test_inputs['color_without_default'], '#00ff00')
        self.assertEqual(test_inputs['hidden_with_default'], 'override')
        self.assertEqual(test_inputs['hidden_without_default'], 'override')
        self.assertEqual(test_inputs['select_1'], 'other')
        self.assertEqual(test_inputs['select_2'], 'other')
        self.assertEqual(test_inputs['section_1.text_with_default'], 'section_override')
        self.assertEqual(test_inputs['section_1.text_without_default'], 'section_override')
        self.assertEqual(test_inputs['section_1.no_name'], 'true')
        self.assertNotIn('section_1', test_inputs)

        # Validate conditionals
        self.assertEqual(test_inputs['cond.text_0'], 'override')
        self.assertEqual(test_inputs['cond.text_1'], 'value_3')
        self.assertNotIn('cond', test_inputs)
        self.assertNotIn('cond.text_2', test_inputs)

        # Validate repeats
        self.assertEqual(
            test_inputs['repeat_1'],
            [
                dict(repeat_integer_with_default='10', repeat_integer_without_default='11'),
            ],
        )
        self.assertEqual(
            test_inputs['repeat_2'],
            [
                dict(repeat_integer_with_default='20', repeat_integer_without_default='21'),
                dict(repeat_integer_with_default='30', repeat_integer_without_default='31'),
            ],
        )
        self.assertEqual(
            [
                key for key in test_inputs
                if key.startswith('repeat_')
            ],
            [
                'repeat_1',
                'repeat_2',
            ],
        )
