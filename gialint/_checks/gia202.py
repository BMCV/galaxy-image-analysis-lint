from Cheetah.Template import Template
from Cheetah.Parser import ParseError


def check(tool_xml_root):
    for path in (
        'command',
        'configfiles/configfile',
    ):
        for template in tool_xml_root.findall(f'./{path}'):
            namespace = dict()
            try:
                Template(template.text, searchList=namespace)
            except ParseError:
                yield template.sourceline
