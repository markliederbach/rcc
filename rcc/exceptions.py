class RCCException(Exception):
    pass


class HTTPException(RCCException):
    pass


class UNMSHTTPException(HTTPException):
    pass


class BreakLoop(RCCException):
    pass
