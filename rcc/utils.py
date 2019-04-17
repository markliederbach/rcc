import signal
from contextlib import contextmanager


@contextmanager
def signal_timeout(time):
    def raise_timeout(*args, **kwargs):
        raise TimeoutError

    signal.signal(signal.SIGALRM, raise_timeout)

    signal.alarm(time)

    try:
        yield False
    except TimeoutError:
        pass
    finally:
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
