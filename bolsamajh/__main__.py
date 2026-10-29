"""Allow running as `python -m bolsamajh` or direct executable entry point."""

import io
import sys


# In Windows GUI / --noconsole / pythonw, sys.stdout and sys.stderr are None.
# Provide safe stream wrappers with .isatty() returning False to prevent
# AttributeError crashes in logging, uvicorn, and third-party libraries.
class _SafeNullStream(io.StringIO):
    def isatty(self) -> bool:
        return False

    def flush(self) -> None:
        pass

    def write(self, s: str) -> int:
        return len(s)


if sys.stdout is None:
    sys.stdout = _SafeNullStream()
if sys.stderr is None:
    sys.stderr = _SafeNullStream()

if __name__ == "__main__":
    from bolsamajh.main import main

    main()
