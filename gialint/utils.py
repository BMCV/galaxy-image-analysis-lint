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
    inputs = dict()  # mps the full name of an input parameter to its raw value (prior to type conversion)
    input_types = dict()  # maps the full name of an input parameter to its type converter
    conditional_inputs = dict()  # maps the full name of a conditional to its first input parameter

    # Parse input parameters, default values, test values, and type converters
    for param in inputs_xml.findall('.//param'):
        full_param_name = get_full_param_name(param)
        converter = None

        # Skip invalid parameters (this is handled by `planemo lint`)
        if (param_type := param.attrib.get('type', '').lower()) == '':
            continue

        # Skip if the parameter is inactive due to a parent conditional
        container = param.getparent()
        is_active = True
        while container.tag not in ('inputs', 'test'):
            if container.tag == 'when' and container.getparent().tag == 'conditional':
                conditional_name = get_full_param_name(container.getparent())
                if conditional_name not in conditional_inputs or (
                    inputs[conditional_inputs[conditional_name]] != container.attrib.get('value')
                ):
                    is_active = False
                    break
            container = container.getparent()
        if not is_active:
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

        # Register the input for a conditional
        if param.getparent().tag == 'conditional':
            conditional_name = get_full_param_name(param.getparent())
            conditional_inputs[conditional_name] = full_param_name

        # Read test value
        if (
            test_param := test_xml.findall(
                './' + '/'.join(f'param[@name="{name}"]' for name in full_param_name.split('.'))
            )
        ):
            inputs[full_param_name] = test_param[0].attrib.get('value')

    # Return inputs and apply type converters
    return {
        key: (
            None if value is None else input_types[key](value)
        ) for key, value in inputs.items()
    }


def list_tests(tool_xml_root):
    yield from tool_xml_root.findall('./tests/test')
