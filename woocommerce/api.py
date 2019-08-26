# -*- coding: utf-8 -*-


__title__ = "woocommerce"
__version__ = "1.0"
__author__ = "UltrafunkAmsterdam"
__license__ = "MIT"
__all__ = ['Api']

import logging
from urllib.parse import urlparse

import requests


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
        self._api_url = f'{self.site_url}/{self._api}/{self._version}'
        self.session = requests.session()
        self.last_response = None
        self.logged_in = False

        self.params = {
            "consumer_key": self._consumer_key,
            "consumer_secret": self._consumer_secret
        }

        self.headers = {
            "user-agent":
                f"WooCommerce API Client-Python/{__version__}",
            "accept":
                "application/json",
            "content-type":
                "application/json;charset=utf-8"
        }
        self.session.headers.update(self.headers)
        self.session.params.update(self.params)
        self._method = None
        self._endpoint = None
        self.login()

    def login(self):
        self._endpoint = 'products'
        self._method = 'get'
        response = self._request()
        if response:
            self.log.debug('authentication successful')
            self.logged_in = True
            return True

    def _request(self, method=None, endpoint=None, params=None, data=None):
        if endpoint:
            self._endpoint = endpoint
        if method:
            self._method = method
        _endpoint = f'{self._api_url}/{self._endpoint}'
        self.log.debug(f'requesting {_endpoint}')
        response = self.session.request(self._method, _endpoint, json=data, params=params)
        if response != self.last_response:
            self.last_response = response
        if self.last_response:
            try:
                return self.last_response.json()
            except:
                pass

    def get(self, endpoint, get_all=False):
        self._method = 'get'
        self._endpoint = endpoint
        if not get_all:
            return self._request()
        return list(self.get_all(endpoint))

    def post(self, endpoint, data):
        self._method = 'post'
        self._endpoint = endpoint
        return self._request(data=data)

    def put(self, endpoint, data):
        self._method = 'put'
        self._endpoint = endpoint
        return self._request(data=data)

    def delete(self, endpoint):
        self._method = 'delete'
        self._endpoint = endpoint
        return self._request()

    def __iter__(self):
        return self.get_all(self._endpoint)

    def get_all(self, endpoint, data=None):
        page = 1
        while True:
            params = {'page': page}
            responses = self._request(method='get', endpoint=endpoint, params=params,data=data)
            if not responses:
                break
           
            for response in responses:
                yield response
            page += 1
       
    def iter_products(self):
         page = 1
         while True:
             params = {'page': page}
             products = self._request('get', 'products', params)
             for product in products:
                 yield product
             page += 1

    def __repr__(self):
        return f'<WooCommerce Api(auth={"YES" if self.logged_in else "NO"}, _endpoint: {self._endpoint}, _method: {self._method.upper()} )>'

    def __str__(self):
        return self.__repr__()
