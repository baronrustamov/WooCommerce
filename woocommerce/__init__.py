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
from urllib.parse import urlparse, parse_qs
import json



class InvalidApiResponse(Exception): pass


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

    def get(self, endpoint, limit=25, page=1):
        qs = parse_qs(urlparse(self._api_url + f'{endpoint}').query)
        per_page = qs.get('per_page') or limit
        pagenum = qs.get('page') or page
        params = {'per_page': per_page , 'page': pagenum}
        endpoint = self._set_endpoint(endpoint)
        try:                      
            r = self._last_response = self._session.get(self._api_url + f'/{endpoint}', params=params)
            r = r.json()
        except Exception as e:
            raise InvalidApiResponse(e) from e
        if isinstance(r, list):
            return [Object(x,self, endpoint) for x in r]
        return Object(r, self, endpoint)

    def post(self, endpoint, json_data):
        endpoint = self._set_endpoint(endpoint)
        try:
            r = self._last_response = self._session.post(self._api_url + f'/{endpoint}', json=json_data)
            r = r.json()
        except Exception as e:
            raise InvalidApiResponse(e) from e
        if isinstance(r, list):
            return [Object(x, self, endpoint) for x in r]
        return Object(r, self, endpoint)


    def put(self, endpoint, json_data):
        endpoint = self._set_endpoint(endpoint)
        try:
            r = self._last_response = self._session.put(self._api_url + f'/{endpoint}', json=json_data)
            r = r.json()
        except Exception as e:
            raise InvalidApiResponse(e) from e
        if isinstance(r, list):
            return [Object(x, self, endpoint) for x in r]
        return Object(r, self)

    def delete(self, endpoint):
        endpoint = self._set_endpoint(endpoint)
        try:
            r = self._last_response = self._session.delete(self._api_url + f'/{endpoint}')
            r = r.json()
        except Exception as e:
            raise InvalidApiResponse(e) from e
        if isinstance(r, list):
            return [Object(x, self, endpoint) for x in r]
        return Object(r, self, endpoint)

    def delete_bulk(self, endpoint, ids):
                              
        req = { 'delete' :  [ {'id': _id} for _id in list(ids) ] }
        try:
            return self.post(endpoint + '/batch', req)
        except Exception as e:
            raise InvalidApiResponse(e) from e

    def generate(self, endpoint):
        page = 1
        while True:
            endpoint = self._set_endpoint(endpoint)
            params = f'?per_page=10&page={page}'
#             params = {'per_page': 10, 'page': page }
            r = self._last_response = self._session.get(self._api_url + f'/{endpoint}/{params}')
            products = r.json()
            if not products:
                break
            for product in products:
                yield Object(product, self, endpoint)
            page += 1


class Object:

    def __init__(self, data, connection=None, endpoint=None):
        self._d = {}
        self._conn = connection
        #if  '/' in endpoint:
        #    endpoint = '/'.join(endpoint.split('/')[:-1])
        self._endpoint = endpoint
        for name, value in data.items():
            setattr(self, name, self._wrap(value))
    
    @property
    def endpoint(self):
        return self._endpoint
 
    @property
    def connection(self):
        return self._conn
    
    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return self.__class__(value, self._conn, self._endpoint) if isinstance(value, dict) else value

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
            if callable(val):
                continue
            if key in ('related_ids',):
                continue
            element = []
            if isinstance(val, list):
                for item in val:
                    element.append(Object._my_dict(item))
            else:
                element = Object._my_dict(val)
            result[key] = element
        return result

    def refresh(self):
        if str(self.id) not in self._endpoint:
            self._endpoint += f'/{str(self.id)}'
        newself = self.connection.get(f'{self._endpoint}')
        self._updatefrom(newself) 
    
    def _updatefrom(self, otherobject=None):
        if isinstance(otherobject, (type(self),)):
            otherobject = otherobject.toDict()
        me = self.toDict()
        for name, value in otherobject.items():
            self._conn._log.debug(f'comparing own {name} with remote {name}')
            if me.get(name) != value:
                self._conn._log.debug(f'UPDATING {name}')
                self._conn._log.debug(f'OWN {name}: {me.get(name)}')
                self._conn._log.debug(f'OTHER {name}: {value}')
                #self._conn._log.debug(f'setting own {name} to match remote version:  own:{me.get(name)} / remote:{value} ')
                  
            #if getattr(self, name) != value:
#                 self._conn._log.info('updating ', str(name), ' with new value ' , str(value))
                setattr(self, name, self._wrap(value))
        
    def commit(self, action='update'):
        """
        action = 'update' (default) -> commit this object to the remote woocommerce instance it came from. 
        If this object is created as new without coming from a woocommerce instance, and should be created
        on the remote site, the action should read 'create'
        if the object needs to be deleted on the remote site, the action should read 'delete'
        """
        answ = None
        if str(self.id) in self._endpoint:
            endpoint = ''.join(self._endpoint.rsplit('/')[0])
        else:
            endpoint = self._endpoint
        try:                
            answ = self._conn.post(f'{endpoint}/batch', { action : [ self.toDict() ] }  )    
            objects = getattr(answ, action)
            if objects[0].id == self.id:
                self.refresh()
                return True
        except Exception as e:
            raise InvalidApiResponse(e) from e
        if hasattr(answ, 'code'):
            raise InvalidApiResponse(answ.code)
        
        # for key in answ.keys():
        #     if key in ('update', 'create', 'delete'):
        #        res = answ.get(key)
        #        if res:
        #            return res
        #        # return False
        # else:
        #     return ans
