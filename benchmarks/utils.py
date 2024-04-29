class _EmitPrinter:
    @staticmethod
    def emit(text):
        print(text)


class StdOutLogger:
    msg = _EmitPrinter()
    msg_error = _EmitPrinter()
