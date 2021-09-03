class InvalidItem(ValueError):
    """Item is not correctly configured in JSON."""


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

    @classmethod
    def from_json(cls, obj):
        raise NotImplementedError

    def to_json(self):
        raise NotImplementedError
