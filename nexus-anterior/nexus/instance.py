"""OS-owned startup lock; existence of the file never means ownership."""
import errno
import os
from contextlib import contextmanager
from pathlib import Path

from nexus.contracts import Blocked


@contextmanager
def data_directory_lock(data_root):
    """Reserve a local data directory before Host can recover its state."""
    root = Path(data_root).resolve()
    lock_path = root / ".nexus.lock"
    try:
        root.mkdir(parents=True, exist_ok=True)
        if lock_path.is_symlink() or lock_path.is_junction():
            raise Blocked("Ficheiro de coordenação redirecionado.")
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as error:
        raise Blocked("Não foi possível abrir a memória Nexus para arranque.") from error
    try:
        # Python opens non-inheritable descriptors; be explicit for tool children.
        os.set_inheritable(descriptor, False)
        try:
            if os.name == "nt":
                import msvcrt
                # A byte range may extend beyond EOF; no pre-lock write is needed.
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise Blocked("Já existe uma Folha Nexus a usar esta memória. Usa a janela aberta.") from error
            raise Blocked("Não foi possível reservar a memória Nexus.") from error
        yield root
    finally:
        # Closing releases the OS lock, including on process termination.
        # Keep the same file/inode so a new launcher cannot bypass a live owner.
        os.close(descriptor)
