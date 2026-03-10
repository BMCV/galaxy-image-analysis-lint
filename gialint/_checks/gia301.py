def check(tool_xml_root, tool_path):
    edam_operations = list(
        tool_xml_root.xpath(f'./edam_operations/edam_operation/text()')
    )
    if 'operation_3443' not in edam_operations:
        yield tool_xml_root.sourceline
