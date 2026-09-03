class ToolFailure(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def invalid(message: str) -> ToolFailure:
    return ToolFailure("INVALID_ARGUMENT", message)
