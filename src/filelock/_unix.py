import os
import sys
from abc import ABC
from typing import cast

from ._api import BaseFileLock

#: a flag to indicate if the fcntl API is available
has_fcntl = False
if sys.platform == "win32":  # pragma: win32 cover

    class UnixFileLock(BaseFileLock, ABC):
        """Uses the :func:`fcntl.flock` to hard lock the lock file on unix systems."""

else:  # pragma: win32 no cover
    try:
        import fcntl
    except ImportError:
        pass
    else:
        has_fcntl = True

    class UnixFileLock(BaseFileLock):
        """Uses the :func:`fcntl.flock` to hard lock the lock file on unix systems."""

        def _acquire(self) -> None:
            open_flags = os.O_RDWR | os.O_CREAT | os.O_TRUNC
            open_mode = 0o660
            umask = 0o002
            original_umask = os.umask(umask)  # change to temp umask and store original umask
            fd = os.open(self._lock_file, open_flags, open_mode)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                os.close(fd)
            else:
                self._lock_file_fd = fd
            finally:
                os.umask(original_umask)  # restore umask

        def _release(self) -> None:
            # Do not remove the lockfile:
            #   https://github.com/tox-dev/py-filelock/issues/31
            #   https://stackoverflow.com/questions/17708885/flock-removing-locked-file-without-race-condition
            fd = cast(int, self._lock_file_fd)
            self._lock_file_fd = None
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)


__all__ = [
    "has_fcntl",
    "UnixFileLock",
]
