def check(tool_xml_root, tool_path):
    for output in tool_xml_root.findall(".//outputs//*"):
        fmt = output.get('format', '').strip().lower()
        if fmt in (
            'csv',
            'tsv',
        ):
            yield output.sourceline
