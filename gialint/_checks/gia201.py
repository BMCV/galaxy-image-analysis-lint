from ..utils import get_full_param_name


def check(tool_xml_root):
    zarr_params = list()
    commands = tool_xml_root.findall('./command')
    command = commands[0].text if commands else None
    for param in tool_xml_root.findall('.//inputs//param[@type="data"]'):
        formats = [fmt.strip().lower() for fmt in param.get('format', '').split(',')]
        if 'zarr' in formats or 'ome.zarr' in formats:
            full_param_name = get_full_param_name(param)
            if command is None or not all(
                (
                    token in command
                    for token in (
                        f'${full_param_name}.extension',
                        f'${full_param_name}.extra_files_path/${full_param_name}.metadata.store_root',
                    )
                )
            ):
                yield param.sourceline
