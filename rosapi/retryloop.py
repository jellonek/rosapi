# retry loop from http://code.activestate.com/recipes/578163-retry-loop/
import time


class RetryError(Exception):
    pass


def retryloop(attempts, timeout):
    starttime = time.time()
    success = set()
    for i in range(attempts): 
        success.add(True)
        yield success.clear
        if success:
            return
        if time.time() > starttime + timeout:
            break
    raise RetryError
