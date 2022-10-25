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


class WikipediaManager(IdentifierManager):
    """This class implements an identifier manager for wikidata identifier"""

    def __init__(self, data={}, use_api_service=True):
        """Wikipedia manager constructor."""
        super(WikipediaManager, self).__init__()
        self._api = "https://en.wikipedia.org/w/api.php/"
        self._use_api_service = use_api_service
        self._p = "wikipedia:"
        self._data = data

    def is_valid(self, wikipedia_id, get_extra_info=False):

        wikipedia_id = self.normalise(wikipedia_id, include_prefix=True)

        if wikipedia_id is None or not self.syntax_ok(wikipedia_id):
            return False
        else:
            if wikipedia_id not in self._data or self._data[wikipedia_id] is None:
                if get_extra_info:
                    info = self.exists(wikipedia_id, get_extra_info=True)
                    self._data[wikipedia_id] = info[1]
                    return (info[0] and self.syntax_ok(wikipedia_id)), info[1]
                self._data[wikipedia_id] = dict()
                self._data[wikipedia_id]["valid"] = True if self.exists(wikipedia_id) and self.syntax_ok(wikipedia_id) else False
                return self.exists(wikipedia_id) and self.syntax_ok(wikipedia_id)
            if get_extra_info:
                return self._data[wikipedia_id].get("valid"), self._data[wikipedia_id]
            return self._data[wikipedia_id].get("valid")

    def normalise(self, id_string, include_prefix=False): # da cambiare

        try:
            if include_prefix:
                wikipedia_string = sub(

                    "\0+", "", sub("\s+", "", unquote(id_string[(id_string.index("wikipedia:") + 1):]))

                )
            else:
                wikipedia_string = sub(
                    "\0+", "", sub("\s+", "", unquote(id_string))
                )
            return "%s%s" % (
                self._p if include_prefix else "",
                wikipedia_string.strip(),
            )
        except:
            # Any error in processing the DOI will return None
            return None

    def syntax_ok(self, id_string):

        if not id_string.startswith("wikipedia:"):
            id_string = "wikipedia:" + id_string
        return True if match("^wikipedia:\\.*$", id_string) else False # definisci regex più precisa!!

    def exists(self, wikipedia_id_full, get_extra_info=False, allow_extra_api=None):
        valid_bool = True

        # -------------------------------------controlla


        if self._use_api_service:
            wikipedia_id = self.normalise(wikipedia_id_full)
            if wikipedia_id is not None:
                tentative = 3
                while tentative:
                    tentative -= 1
                    try:
                        # TO GET BASIC (STRUCTURED) INFO ABOUT THE PAGE
                        query_params = {
                            "action": "query",
                            "prop": "info",
                            "titles": wikipedia_id, # use this if the id input by the user is the page TITLE
                            #"pageids" : wikipedia_id, # use this if the id input by the user is the PAGE ID
                            "format": "json",
                        }

                        # # TO GET FULL (PARSED) CONTENT OF THE PAGE
                        # query_params = {
                        #     "action": "parse",
                        #     "page": wikipedia_id, # use this if the id input by the user is the page TITLE
                        #     #"pageid" : wikipedia_id, # use this if the id input by the user is the PAGE ID
                        #     "format": "json",
                        # }
                        r = get(self._api, params=query_params, headers=self._headers, timeout=30) # controlla
                        if r.status_code == 200:
                            r.encoding = "utf-8"
                            json_res = loads(r.text)
                            valid_bool = True # poi togli e sostituisci il return corretto (da scrivere condizioni per cui sia True)
                            if get_extra_info:
                                return valid_bool, self.extra_info(json_res)
                            return valid_bool # poi togli e sostituisci il return corretto (da scrivere)
                            # return True if json_res['entities'][f"{wikipedia_id}"]['id'] == str(wikipedia_id) else False
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
                valid_bool=False
            else:
                if get_extra_info:
                    return False, {"valid": False}
                return False

        if get_extra_info:
            return valid_bool, {"valid": valid_bool}
        return valid_bool

    def extra_info(self, api_response, choose_api=None, info_dict={}):
        result = {}
        result["valid"] = True
        # to be implemented
        return result
