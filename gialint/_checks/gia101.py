def check(tree, error):
    root = tree.getroot()
    for param in root.findall(".//inputs//param[@type='data']"):
        formats = [fmt.strip().lower() for fmt in param.get('format').split(',')]
        if (
            ('tabular' in formats) != ('tsv' in formats) or
            ('csv' in formats and 'tsv' not in formats)
        ):
            error.line = param.sourceline
            raise error
