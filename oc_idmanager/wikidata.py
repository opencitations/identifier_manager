#!python
# Copyright 2019, Silvio Peroni <essepuntato@gmail.com>
# Copyright 2022, Giuseppe Grieco <giuseppe.grieco3@unibo.it>, Arianna Moretti <arianna.moretti4@unibo.it>, Elia Rizzetto <elia.rizzetto@studio.unibo.it>, Arcangelo Massari <arcangelo.massari@unibo.it>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.


from re import sub, match
from urllib.parse import unquote, quote
from requests import get
from json import loads
from requests import ReadTimeout
from requests.exceptions import ConnectionError
from time import sleep
from oc_idmanager.base import IdentifierManager


class WikidataManager(IdentifierManager):
    """This class implements an identifier manager for wikidata identifier"""

    def __init__(self, data={}, use_api_service=True):
        """Wikidata manager constructor."""
        super(WikidataManager, self).__init__()
        self._api = "https://www.wikidata.org/wiki/Special:EntityData/"
        self._use_api_service = use_api_service
        self._p = "wikidata:"
        self._data = data

    def is_valid(self, wikidata_id, get_extra_info=False):
        wikidata_id = self.normalise(wikidata_id, include_prefix=True)

        if wikidata_id is None or not self.syntax_ok(wikidata_id):
            return False
        else:
            if wikidata_id not in self._data or self._data[wikidata_id] is None:
                if get_extra_info:
                    info = self.exists(wikidata_id, get_extra_info=True)
                    self._data[wikidata_id] = info[1]
                    return (info[0] and self.syntax_ok(wikidata_id)), info[1]
                self._data[wikidata_id] = dict()
                self._data[wikidata_id]["valid"] = True if self.exists(wikidata_id) and self.syntax_ok(wikidata_id) else False
                return self.exists(wikidata_id) and self.syntax_ok(wikidata_id)
            if get_extra_info:
                return self._data[wikidata_id].get("valid"), self._data[wikidata_id]
            return self._data[wikidata_id].get("valid")

    def normalise(self, id_string, include_prefix=False):

        id_string = id_string.upper()
        try:
            wikidata_string = sub(
                "\0+", "", sub("\s+", "", unquote(id_string[id_string.index("Q"):]))
            )
            return "%s%s" % (
                self._p if include_prefix else "",
                wikidata_string.strip(),
            )
        except:
            # Any error in processing the DOI will return None
            return None

    def syntax_ok(self, id_string):

        if not id_string.startswith("wikidata:"):
            id_string = "wikidata:"+id_string
        return True if match("^wikidata:Q[1-9]\\d*$", id_string) else False

    def exists(self, wikidata_id_full, get_extra_info=False):
        valid_bool = True
        if self._use_api_service:
            wikidata_id = self.normalise(wikidata_id_full)
            if wikidata_id is not None:
                tentative = 3
                while tentative:
                    tentative -= 1
                    try:
                        r = get(self._api + quote(wikidata_id), headers=self._headers, timeout=30)
                        if r.status_code == 200:
                            r.encoding = "utf-8"
                            json_res = loads(r.text)
                            if get_extra_info:
                                return True if json_res['entities'][f"{wikidata_id}"]['id'] == str(
                                    wikidata_id) else False, self.extra_info(json_res)
                            return True if json_res['entities'][f"{wikidata_id}"]['id'] == str(wikidata_id) else False
                        elif 400 <= r.status_code < 500:
                            if get_extra_info:
                                return False, {"valid": False}
                            return False
                    except ReadTimeout:
                        # Do nothing, just try again
                        pass
                    except ConnectionError:
                        # Sleep 5 seconds, then try again
                        sleep(5)
                valid_bool = False
            else:
                if get_extra_info:
                    return False, {"valid": False}
                return False

        if get_extra_info:
            return valid_bool, {"valid": valid_bool}
        return valid_bool

    def extra_info(self, api_response):
        result = {}
        result["valid"] = True
        # to be implemented
        return result
