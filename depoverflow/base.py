import asyncio


class InvalidJSONItem(ValueError):
    """Item is not correctly configured in JSON."""


class InvalidReference(ValueError):
    """URL is not this kind of reference."""


class Item(object):
    """Base class for things that can be referenced.
    """
    @classmethod
    def is_url_reference(cls, url):
        raise NotImplementedError

    @classmethod
    def create(cls, url):
        raise NotImplementedError

    def url(self):
        raise NotImplementedError

    def refresh(self):
        raise NotImplementedError

    @classmethod
    def from_json(cls, obj):
        raise NotImplementedError

    def to_json(self):
        raise NotImplementedError


class Batches(object):
    def __init__(self):
        self._batches = []
        self._flushed = False

    def register(self, processor):
        queries = []
        self._batches.append((processor, queries))

        def wrapper(query):
            future = asyncio.Future()
            if self._flushed:
                processor([(query, future)])
            else:
                queries.append((query, future))
            return future

        return wrapper

    def flush(self):
        self._flushed = True
        for processor, queries in self._batches:
            processor(queries)


batching = Batches()
