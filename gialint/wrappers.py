#class ToolParameterValueWrapper:
#    """
#    Mocks `galaxy.tools.wrappers.ToolParameterValueWrapper` naively.
#    """
#
#    value: Optional[Union[str, list[str]]]
#    input: "ToolParameter"
#
#    def __bool__(self) -> bool:
#        return bool(self.value)
#
#    __nonzero__ = __bool__
#
#    def get_display_text(self, quote: bool = True) -> str:
#        """
#        Returns a string containing the value that would be displayed to the user in the tool interface.
#        When quote is True (default), the string is escaped for e.g. command-line usage.
#        """
#        rval = self.input.value_to_display_text(self.value) or ""
#        if quote:
#            return shlex.quote(rval)
#        return rval


class InputValueWrapper:
    """
    Mocks `galaxy.tools.wrappers.InputValueWrapper` naively.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, InputValueWrapper):
            return self.value == other.value
        else:
            return self.value == other

    def __iter__(self):
        return iter(self.value.iter)

    def __gt__(self, other) -> bool:
        if isinstance(other, InputValueWrapper):
            return self.value > other.value
        else:
            return self.value > other

    def __int__(self) -> int:
        return int(float(self))

    def __float__(self) -> float:
        return float(str(self))
