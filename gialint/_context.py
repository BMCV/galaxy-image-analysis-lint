class Context(BaseException):
    
    def __init__(self, code, description, filepath, line):
        super().__init__(description)
        self.code = code
        self.description = description
        self.filepath = filepath
        self.line = line

    def __str__(self):
        where = str(self.filepath)
        if self.line is not None:
            where += f':{self.line}'
        return f'{where} {self.description} ({self.code})'
