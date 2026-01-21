import pathlib

from lxml import etree


def _list_parents(node, include_self=False, stop_at=('inputs', 'test', 'repeat')):
    current = node
    while current is node or current.tag not in stop_at:
        if current is not node or include_self:
            yield current
        current = current.getparent()


def get_full_name(node):
    tokens = list()
    for p in _list_parents(node, include_self=True):
        if (p_name := p.get('name')):
            tokens.append(p_name)
        elif len(tokens) == 0 and (p_argument := p.get('argument')):
            tokens.append(p_argument.removeprefix('--').replace('-', '_'))
    return '.'.join(tokens[::-1])


def _create_boolean_converter(param):
    def _type(checked):
        return param.attrib.get(f'{checked}value', checked)
    return _type


def _get_node_by_name(full_name, root_xml, multiple: bool = False):
    nodes = root_xml.findall(
        './' + '/'.join(f'*[@name="{name}"]' for name in full_name.split('.'))
    )
    if multiple:
        return nodes
    else:
        return nodes[0] if nodes else None


class InputDataset:

    class Metadata:
        pass

    class ZarrMetadata(Metadata):
        def store_root(self):
            return 'store_root'

    def __init__(self, filepath: str):
        self._filepath = filepath

    def __str__(self) -> str:
        return self._filepath

    def extension(self) -> str:
        name = pathlib.Path(self._filepath).name
        return '.'.join(name.split('.')[1:]).lower()

    def ext(self) -> str:
        return self.extension()

    def name(self) -> str:
        return pathlib.Path(self._filepath).name

    def id(self) -> str:
        return str(hash(self._filepath))

    def element_identifier(self) -> str:
        return self.id()

    def extra_files_path(self) -> str:
        return self._filepath

    def metadata(self):
        match self.extension():
            case 'zarr' | 'ome_zarr':
                return self.ZarrMetadata()
            case _:
                return self.Metadata()

    @staticmethod
    def converter(multiple: bool = False):
        def _converter(value: str):
            if multiple:
                return [
                    InputDataset(filepath) for filepath in value.split(',')
                ]
            else:
                return InputDataset(value)
        return _converter


def get_test_inputs(inputs_root, test_root):
    inputs = dict()  # mps the full name of an input parameter to its raw value (prior to type conversion)
    input_types = dict()  # maps the full name of an input parameter to its type converter
    conditional_inputs = dict()  # maps the full name of a conditional to its first input parameter

    # Parse input parameters, default values, test values, and type converters
    for node in inputs_root.xpath('.//param | .//repeat'):
        full_node_name = get_full_name(node)
        converter = None

        # Ignore the `node` if it is an ancestor of a `repeat` block (those are handled explicitly below),
        # but ignore the tag of the root node
        is_repeat_ancestor = False
        for container in _list_parents(node, stop_at=tuple()):
            if container is inputs_root:
                break
            if container.tag == 'repeat':
                is_repeat_ancestor = True
                break
        if is_repeat_ancestor:
            continue

        # Skip if the parameter is inactive due to a parent conditional
        is_active = True
        for container in _list_parents(node):
            if container.tag == 'when' and container.getparent().tag == 'conditional':
                conditional_name = get_full_name(container.getparent())
                if (
                    conditional_name not in conditional_inputs or
                    conditional_inputs[conditional_name] not in inputs or (
                        inputs[conditional_inputs[conditional_name]] != container.attrib.get('value')
                    )
                ):
                    is_active = False
                    break
        if not is_active:
            continue

        # Handle `repeat` blocks recursively
        if node.tag == 'repeat':
            if len(inputs.setdefault(full_node_name, list())) == 0:
                if (test_repeat_nodes := _get_node_by_name(full_node_name, test_root, multiple=True)):
                    for test_repeat_node in test_repeat_nodes:
                        inputs[full_node_name].append(get_test_inputs(node, test_repeat_node))
                else:
                    for input_repeat_node in _get_node_by_name(full_node_name, inputs_root, multiple=True):
                        inputs[full_node_name].append(get_test_inputs(input_repeat_node, etree.Element('repeat')))
                input_types[full_node_name] = list
            continue

        # Skip invalid parameters (this is handled by `planemo lint`)
        if (param_type := node.attrib.get('type', '').lower()) == '':
            continue

        # Read the value from the `value` attribute
        if param_type in ('text', 'integer', 'float', 'color', 'hidden', 'data'):
            inputs[full_node_name] = node.attrib.get('value')
            if param_type == 'data':
                converter = InputDataset.converter(
                    node.attrib.get('multiple', '').lower() == 'true',
                )

        # Read the value from the `checked` attribute
        if param_type in ('boolean',):
            inputs[full_node_name] = node.attrib.get('checked', 'false')
            converter = _create_boolean_converter(node)

        # Read the value from children elements
        if (default_options := node.xpath('./option[translate(@selected, "TRUE", "true")="true"]')):
            inputs[full_node_name] = default_options[0].attrib.get('value')

        # Register type converter
        input_types[full_node_name] = converter or str

        # Register the input for a conditional
        if node.getparent().tag == 'conditional':
            conditional_name = get_full_name(node.getparent())
            conditional_inputs[conditional_name] = full_node_name

        # Read test value
        if (test_param := _get_node_by_name(full_node_name, test_root)) is not None:
            inputs[full_node_name] = test_param.attrib.get('value')

    # Return inputs and apply type converters
    return {
        key: (
            None if value is None else input_types[key](value)
        ) for key, value in inputs.items()
    }


def list_tests(tool_xml_root):
    yield from tool_xml_root.findall('./tests/test')


class Output:

    def __init__(self, name: str):
        self._name = name

    def __str__(self) -> str:
        return self._name

    def files_path(self) -> str:
        return f'${self._name}.files_path'


def get_base_namespace(tool_xml_root):
    ns = {
        '__tool_directory__': '$__tool_directory__',
        'input': None,  # shadow the built-in `input` because it causes hang-ups
    }
    for configfile in tool_xml_root.xpath('./configfiles/*[self::configfile or self::inputs]'):
        if (name := configfile.attrib.get('name')):
            ns[name] = f'${name}'
    for output in tool_xml_root.findall('./outputs/data'):
        if (name := output.attrib.get('name')):
            ns[name] = Output(name)
    return ns


def flat_dict_to_nested(flat_dict):
    root = dict()
    for key, value in flat_dict.items():
        path = key.split('.')

        # Find/create the parent `dict` of where `value` must go
        current = root
        for token in path[:-1]:
            current = current.setdefault(token, dict())

        # Put `value` into the hierarchy
        current[path[-1]] = value
    return root
