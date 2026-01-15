def check(tool_xml_root):
    for param in tool_xml_root.findall(".//inputs//param[@type='data']"):
        formats = [fmt.strip().lower() for fmt in param.get('format', '').split(',')]
        if (
            ('tabular' in formats) != ('tsv' in formats) or
            ('csv' in formats and 'tsv' not in formats)
        ):
            yield param.sourceline
