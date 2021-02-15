# -*- coding: utf-8 -*-

import logging
from urllib.parse import urlparse

from collections.abc import Mapping
import requests
from . import __version__


__all__ = ["Api"]


class Api(object):
    def __init__(
            self,
            site_url,
            consumer_key=None,
            consumer_secret=None,
            api="wp-json",
            version="wc/v3",
            debug=False,
    ):
        """
        Constructs an Api instance

        Args:
            site_url (str): the base site url (no paths!)
            consumer_key (str): api consumer key
            consumer_secret (str): api consumer secret
            api (str): api name (defaults to wp-json)
            version (str): version name (defaults to wc/v3)
        Examples:
            >>> api = Api('https://somesite.com', 'CK_string', 'CS_string')

        """
        self.log = logging.getLogger(self.__class__.__name__)
        if debug:
            self.log.setLevel(10)
        p = urlparse(site_url)
        if p.path:
            site_url = site_url.split(p.path)[0]
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self.site_url = site_url
        self._version = version
        self._api = api
        self._api_url = f"{self.site_url}/{self._api}/{self._version}"
        self.session = requests.session()
        self.last_response = None
        self.logged_in = False

        self.params = {
            "consumer_key": self._consumer_key,
            "consumer_secret": self._consumer_secret,
        }

        self.headers = {
            "user-agent": f"WooCommerce API Client-Python/{__version__}",
            "accept": "application/json",
            "content-type": "application/json;charset=utf-8",
        }
        self.session.headers.update(self.headers)
        self.session.params.update(self.params)
        self._method = None
        self._endpoint = None
        # self.login()

    @property
    def endpoint(self):
        return self._endpoint

    def login(self):
        self._endpoint = "products"
        self._method = "get"
        response = self._request()
        if response:
            self.log.debug("authentication successful")
            self.logged_in = True
            return True

    def _request(self, endpoint, method="GET", params=None, data=None):
        self._endpoint = endpoint
        _endpoint = f"{self._api_url}/{self._endpoint}"
        self.log.debug(f"requesting {_endpoint}")
        response = self.session.request(method, _endpoint, json=data, params=params)
        if response:
            try:
                json_response = response.json()
                if isinstance(json_response, list):
                    return [rdict(item, self) for item in json_response]
                return rdict(json_response, self)
            except:  # noqa
                raise
            finally:
                self.last_response = response

    def get(self, endpoint, limit=100, params=None):
        if not params:
            params = {}
        params.update(dict(limit=limit))
        return self._request(endpoint, params=params)

    def post(self, endpoint, data):
        return self._request(endpoint, "post", data=data)

    def put(self, endpoint, data):
        return self._request(endpoint, "put", data=data)

    def delete(self, endpoint, data=None):
        return self._request(endpoint, "delete", data=data)

    def __iter__(self, s=False):
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        pass

    def get_all(self, endpoint, data=None):
        page = 1
        while True:
            params = {"page": page}
            responses = self._request(endpoint, method="get", params=params, data=data)
            if not responses:
                break
            for response in responses:
                yield response
            page += 1

    def iter(self, endpoint):
        page = 1
        while True:
            params = {"page": page, "per_page": 10}
            items = self._request(endpoint, "get", params)
            if not items:
                break
            for item in items:
                yield item
            page += 1

    def __repr__(self):
        return f"<WooCommerce Api(site_url={self.site_url}, valid={self.logged_in})>"

    def __str__(self):
        return self.__repr__()





def rdict(obj, api):
    retv = RDict(obj)
    retv.api = api
    return retv


def change_notifier(cls):
    memory = dict()
    listeners = dict()

    def addListener(self, callback):  # noqa
        listeners[id(callback)] = callback
        return id(callback)

    def removeListener(self, id):  # noqa
        del listeners[id]

    def notifyListeners(self):  # noqa
        for i, listener in listeners.items():
            try:
                listener(memory)
            except Exception as e:
                logging.warning(e)

    @property
    def changed(self):
        if "api" in memory:
            del memory["api"]
        return memory

    def __setattr__(self, item, val):
        memory[item] = val
        self.notifyListeners()
        return object.__setattr__(self, item, val)

    def __setitem__(self, item, val):
        memory[item] = val
        self.notifyListeners()
        return dict.__setitem__(self, item, val)

    def __delitem__(self, item):
        if item in memory:
            del memory[item]
            self.notifyListeners()
        return dict.__delitem__(self, item)

    def __delattr__(self, item):
        if item in memory:
            del memory[item]
            self.notifyListeners()
        return object.__delattr__(self, item)

    cls.changed = changed
    cls.__setattr__ = __setattr__
    cls.__setitem__ = __setitem__
    cls.__delitem__ = __delitem__
    cls.__delattr__ = __delattr__
    cls.notifyListeners = notifyListeners
    cls.addListener = addListener
    cls.removeListener = removeListener
    return cls


@change_notifier
class RDict(dict):
    def __init__(self, *a, **kw):
        """
        This object represents an item from the API (product, order, etc).
        modifications are being saved, and once completed, a call to .commit()
        will apply the changes on your site/backend. To see what is changed,
        a call to .changed can be made.

        :param a:
        :param kw:
        """
        super().__init__(*a, **kw)
        dict.__setattr__(self, "__dict__", self)

    def _wrap(self, val):
        if isinstance(val, Mapping):
            if not isinstance(val, RDict):
                return RDict(val)
        elif isinstance(val, (list, set, frozenset, tuple)):
            return [self.__class__(i) if isinstance(i, Mapping) else i for i in val]
        else:
            return val

    def __setattr__(self, item, val):
        return dict.__setattr__(self, item, self._wrap(val))

    def __setitem__(self, item, val):
        return dict.__setitem__(self, item, self._wrap(val))

    def commit(self):
        if "api" in self:
            if "id" in self:
                changed = self.changed
                if "api" in changed:
                    del changed["api"]
                return self.api.put(f"{self.api.endpoint}/{self.id}", changed)

    def __repr__(self):
        return "<%s{ %s }>" % (
            self.__class__.__name__,
            "\n\t".join(
                "%s : %s" % (k, "\t" + repr(v) if isinstance(v, dict) else repr(v))
                for (k, v) in self.items()
            ),
        )
