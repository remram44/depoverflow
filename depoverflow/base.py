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

    @classmethod
    def from_json(cls, obj):
        raise NotImplementedError

    def to_json(self):
        raise NotImplementedError
