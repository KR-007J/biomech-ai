class _PatchedResponse:
    def __init__(self, status=200):
        self.status = status


class ClientResponse(_PatchedResponse):
    pass


class ClientError(Exception):
    pass


class _RequestContextManager:
    def __init__(self, response=None):
        self._response = response or _PatchedResponse()

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class ClientSession:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def post(self, *args, **kwargs):
        return _RequestContextManager()
