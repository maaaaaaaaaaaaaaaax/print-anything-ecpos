class PrinterError(Exception):
    pass


class PrinterConnectionError(PrinterError):
    pass


class PrinterExecutionError(PrinterError):
    pass


class PrinterClosedError(PrinterError):
    pass


class ProfileError(PrinterError):
    pass
