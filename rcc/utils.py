import time
import signal
import logging
from contextlib import contextmanager
from rcc.exceptions import BreakLoop, UNMSHTTPException


logger = logging.getLogger(__name__)


@contextmanager
def signal_timeout(time_sec):
    def raise_timeout(*args, **kwargs):
        raise TimeoutError

    signal.signal(signal.SIGALRM, raise_timeout)

    signal.alarm(time_sec)

    try:
        yield False
    except TimeoutError:
        pass
    finally:
        signal.signal(signal.SIGALRM, signal.SIG_IGN)


def do_until(func, timeout, interval, *args, **kwargs):
    timeout_raised = True
    with signal_timeout(timeout):
        while True:
            try:
                func(*args, **kwargs)
                time.sleep(interval)
            except BreakLoop:
                timeout_raised = False
                break
    return timeout_raised


def check_dns(http_client, ip_client, public_ip_address):
    dns_result = ip_client.dns_lookup(http_client.get_domain())
    if dns_result == public_ip_address:
        raise BreakLoop


def check_unms(unms_client, device_id):
    try:
        response = unms_client.get_device(device_id)
        if response.status_code == 200:
            raise BreakLoop
        else:
            logger.warning("UNMS has started, but isn't ready yet. Waiting...")
    except UNMSHTTPException:
        logger.warning(f"UNMS is not yet reachable. Waiting...")
