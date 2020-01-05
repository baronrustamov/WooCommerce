# -*- coding: utf-8 -*-

"""

██╗    ██╗ ██████╗  ██████╗  ██████╗ ██████╗ ███╗   ███╗███╗   ███╗███████╗██████╗  ██████╗███████╗
██║    ██║██╔═══██╗██╔═══██╗██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔════╝██╔══██╗██╔════╝██╔════╝
██║ █╗ ██║██║   ██║██║   ██║██║     ██║   ██║██╔████╔██║██╔████╔██║█████╗  ██████╔╝██║     █████╗
██║███╗██║██║   ██║██║   ██║██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══╝  ██╔══██╗██║     ██╔══╝
╚███╔███╔╝╚██████╔╝╚██████╔╝╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║███████╗██║  ██║╚██████╗███████╗
 ╚══╝╚══╝  ╚═════╝  ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝╚══════╝


"""

__title__ = "woocommerce"
__version__ = "1.1"
__author__ = "UltrafunkAmsterdam"
__license__ = "MIT"
__all__ = ['Api', 'Object']

import logging
import requests
from urllib.parse import urlparse
import json


class Api(object):

    def __init__(self, site_url, consumer_key=None, consumer_secret=None, api='wp-json', version='wc/v3', debug=False):
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

        self._log = logging.getLogger(self.__class__.__name__)
        if debug:
            self._log.setLevel(10)
        p = urlparse(site_url)
        if p.path:
            site_url = site_url.split(p.path)[0]
        self._consumer_key = consumer_key
        self._consumer_secret = consumer_secret
        self._site_url = site_url
        self._version = version
        self._api = api
        self._api_url = f'{self._site_url}/{self._api}/{self._version}'
        self._session = requests.session()
        self._last_response = None
        self._logged_in = False

        self._params = {
            "consumer_key": self._consumer_key,
            "consumer_secret": self._consumer_secret
        }

        self._headers = {
            "user-agent":
                f"WooCommerce API Client-Python/{__version__}",
            "accept":
                "application/json",
            "content-type":
                "application/json;charset=utf-8"
        }

        self._session.headers.update(self._headers)
        self._session.params.update(self._params)

    @property
    def authenticated(self):
        r = self._session.get(self._api_url + f'/{self._set_endpoint("products")}')
        if r.status_code != 200:
            return False
        return True


    def _set_endpoint(self, endpoint):
        return endpoint[1:] if endpoint[0] == '/' else endpoint

    def get(self, endpoint, limit=25):
        params = {'per_page': limit }
        endpoint = self._set_endpoint(endpoint)
        r = self._last_response = self._session.get(self._api_url + f'/{endpoint}', params=params)
        r = r.json()
        if isinstance(r, list):
            return [Object(x,self) for x in r]
        return Object(r, self)

    def post(self, endpoint, json_data):
        endpoint = self._set_endpoint(endpoint)
        r = self._last_response = self._session.post(self._api_url + f'/{endpoint}', json=json_data)
        r = r.json()
        if isinstance(r, list):
            return [Object(x, self) for x in r]
        return Object(r, self)


    def put(self, endpoint, json_data):
        endpoint = self._set_endpoint(endpoint)
        r = self._last_response = self._session.put(self._api_url + f'/{endpoint}', json=json_data)
        r = r.json()
        if isinstance(r, list):
            return [Object(x, self) for x in r]
        return Object(r, self)

    def delete(self, endpoint):
        endpoint = self._set_endpoint(endpoint)
        r = self._last_response = self._session.delete(self._api_url + f'/{endpoint}')
        r = r.json()
        if isinstance(r, list):
            return [Object(x, self) for x in r]
        return Object(r, self)

    def delete_bulk(self, endpoint, ids):
        req = { 'delete' :  [ {'id': _id} for _id in list(ids) ] }
        return self.post(endpoint + '/batch', req)


    def generate(self, endpoint):
        page = 1
        while True:
            params = f'?per_page=10&page={page}'
#             params = {'per_page': 10, 'page': page }
            r = self._last_response = self._session.get(self._api_url + f'/{endpoint}/{params}')
            products = r.json()
            if not products:
                break
            for product in products:
                yield Object(product, self)
            page += 1


class Object:

    def __init__(self, data, conn=None):
        self._d = {}
        for name, value in data.items():
            setattr(self, name, self._wrap(value))
        self.conn = conn


    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return self.__class__(value) if isinstance(value, dict) else value

    def toDict(self):
        return self._my_dict(self)

    def toJson(self):
        return json.dumps(self.toDict())

    @classmethod
    def fromDict(cls, d):
        return cls(d)

    @classmethod
    def fromJson(cls, j):
        import json
        return cls(json.loads(j))

    @staticmethod
    def _my_dict(obj):
        if not hasattr(obj, "__dict__"):
            return obj
        result = {}
        for key, val in obj.__dict__.items():
            if key.startswith("_"):
                continue
            element = []
            if isinstance(val, list):
                for item in val:
                    element.append(Object._my_dict(item))
            else:
                element = Object._my_dict(val)
            result[key] = element
        return result

                              
    def update_remote(self):
        try:
            answ = self.conn.put(f'products/batch', [ { 'update' : [ self.toDict() ] } ]
        except Exception as e:
            print(e)
            return self._last_response.json()

        for key in answ.keys():
            if key in ('update', 'create', 'delete'):
               res = answ.get(key)
               if res:
                   return res
               # return False
        else:
            return answ
