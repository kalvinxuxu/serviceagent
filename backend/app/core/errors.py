class ComponentError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message

class ValidationError(ComponentError):
    pass

class ToolUnavailableError(ComponentError):
    pass
