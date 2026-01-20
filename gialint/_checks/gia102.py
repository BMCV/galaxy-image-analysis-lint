def check(tool_xml_root):
    for path in (
        'inputs//param[@type="data"]',
        'outputs/data',
    ):
        for param in tool_xml_root.findall(f'.//{path}'):
            formats = [fmt.strip().lower() for fmt in param.get('format', '').split(',')]
            if 'tif' in formats or param.get('from_work_dir', '').strip().lower().endswith('.tif'):
                yield param.sourceline
    for param in tool_xml_root.findall('.//tests/test//param'):
        if param.get('ftype', '').strip().lower() == 'tif' or param.get('value', '').strip().lower().endswith('.tif'):
            yield param.sourceline
