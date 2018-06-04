from urllib import parse
from typing import Dict, List


class featureRequest(object):

    def __init__(self, method: str, url: str, encoding='utf-8', headers_to_exclude=None,
                 params_to_exclude=None):
        self.method = method                # type: str
        self.url = url                      # type: str
        self.label_type = ''                # type: str
        self.label_attack = ''              # type: str
        self.original_str = ''              # type: str
        self._encoding = encoding           # type: str
        self._headers = {}                  # type: Dict[str, str]
        self._query_params = {}             # type: Dict[str, str]
        self._body_params = {}              # type: Dict[str, str]

        self._headers_to_exclude = headers_to_exclude
        self._params_to_exclude = params_to_exclude

    def __str__(self) -> str:
        return '{} {}'.format(self.method, self.url)

    @property
    def label(self) -> str:
        return '{} {}'.format(self.label_type, self.label_attack).strip()

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers

    @headers.setter
    def headers(self, s: str):
        self._headers = _split(s, '\n', ': ', self._headers_to_exclude)

    @property
    def query_params(self) -> Dict[str, str]:
        return self._query_params

    @query_params.setter
    def query_params(self, s: str):
        d = _split(s, '&', '=', self._params_to_exclude)
        self._query_params = {
            k: parse.unquote_plus(v, encoding=self._encoding)
            for k, v in d.items()}

    @property
    def body_params(self) -> Dict[str, str]:
        return self._body_params

    @body_params.setter
    def body_params(self, s: str):
        d = _split(s, '&', '=', self._params_to_exclude)
        self._body_params = {
            k: parse.unquote_plus(v, encoding=self._encoding)
            for k, v in d.items()}

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if (self.method == other.method
                    and self.url == other.url
                    and self.headers == other.headers
                    and self.query_params == other.query_params
                    and self.body_params == other.body_params):
                return True
            return False
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self == other
        return NotImplemented

def _split(input_s: str, sep_1: str, sep_2: str, blacklist: List[str]) -> Dict:
    d = {}

    if input_s:
        for e in input_s.split(sep_1):
            e = e.strip()

            if e:
                try:
                    k, v = e.split(sep_2, maxsplit=1)   # will raise error if sep is not present
                    k = k.strip().lower()               # all keys in lowercase
                    v = v.strip()
                    d[k] = v                    # in case of repeated keys, holds only the last one
                except ValueError:
                    pass

    if blacklist:
        # remove some keys
        for k in blacklist:
            d.pop(k, None)

    return d