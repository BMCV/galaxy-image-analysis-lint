_types = {
    'text': str,
    'integer': int,
    'float': float,
    'color': str,
    'hidden': str,
    'select': str,
}


def get_full_param_name(param_xml):
    tokens = []
    current = param_xml
    while current.tag not in ('inputs', 'test'):
        if current_name := current.get('name'):
            tokens.append(current_name)
        current = current.getparent()
    return '.'.join(tokens[::-1])


def _create_boolean_converter(param):
    def _type(checked):
        return param.attrib.get(f'{checked}value', checked)
    return _type


def get_test_inputs(inputs_xml, test_xml):
    inputs = dict()
    input_types = dict()

    # Parse input parameters, default values, and type converters
    for param in inputs_xml.findall('.//param'):
        full_param_name = get_full_param_name(param)
        converter = None

        # Skip invalid parameters (this is handled by `planemo lint`)
        if (param_type := param.attrib.get('type', '').lower()) == '':
            continue

        # Read the value from the `value` attribute
        if param_type in ('text', 'integer', 'float', 'color', 'hidden'):
            inputs[full_param_name] = param.attrib.get('value')

        # Read the value from the `checked` attribute
        if param_type in ('boolean',):
            inputs[full_param_name] = param.attrib.get('checked', 'false')
            converter = _create_boolean_converter(param)

        # Read the value from children elements
        if (default_options := param.findall('./option[@selected="true"]')):
            inputs[full_param_name] = default_options[0].attrib.get('value')

        # Register type converter
        input_types[full_param_name] = converter or _types.get(param_type)

    # Parse test parameters
    for param in test_xml.findall('.//param'):
        full_param_name = get_full_param_name(param)

        # Skip invalid parameters (this is handled by `planemo lint`)
        if full_param_name not in inputs:
            continue

        # Read the value from the `value` attribute
        inputs[full_param_name] = param.attrib.get('value')

    # Return inputs and apply type converters
    return {
        key: (
            None if value is None else input_types[key](value)
        ) for key, value in inputs.items()
    }


def list_tests(tool_xml_root):
    yield from tool_xml_root.findall('./tests/test')
