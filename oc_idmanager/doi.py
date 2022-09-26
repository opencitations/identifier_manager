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
import re
from re import sub, match
from urllib.parse import unquote, quote
from requests import get
from json import loads
from requests import ReadTimeout
from requests.exceptions import ConnectionError
from time import sleep
from oc_idmanager.base import IdentifierManager


class DOIManager(IdentifierManager):
    """This class implements an identifier manager for doi identifier"""

    def __init__(self, data={}, use_api_service=True):
        """DOI manager constructor."""
        super(DOIManager,self).__init__()
        self._api = "https://doi.org/api/handles/"
        self._use_api_service = use_api_service
        self._p = "doi:"
        self._data = data

    def is_valid(self, id_string, get_extra_info=False):
        doi = self.normalise(id_string, include_prefix=True)

        if doi is None:
            return False
        else:
            if doi not in self._data or self._data[doi] is None:
                if get_extra_info:
                    info = self.exists(doi, get_extra_info=True)
                    self._data[doi] = info[1]
                    return (info[0] and self.syntax_ok(doi)), info[1]
                self._data[doi] = dict()
                self._data[doi]["valid"] = True if self.exists(doi) and self.syntax_ok(doi) else False
                return self.exists(doi) and self.syntax_ok(doi)
            if get_extra_info:
                return self._data[doi].get("valid"), self._data[doi]
            return self._data[doi].get("valid")

    def normalise(self, id_string, include_prefix=False):
        try:
            doi_string = sub(
                "\0+", "", sub("\s+", "", unquote(id_string[id_string.index("10.") :]))
            )
            return "%s%s" % (
                self._p if include_prefix else "",
                doi_string.lower().strip(),
            )
        except:
            # Any error in processing the DOI will return None
            return None

    def syntax_ok(self, id_string):
        if not id_string.startswith(self._p):
            id_string = self._p+id_string
        return True if match("^doi:10\.(\d{4,9}|[^\s/]+(\.[^\s/]+)*)/[^\s]+$", id_string, re.IGNORECASE) else False

    def exists(self, doi_full, get_extra_info=False):
        if self._use_api_service:
            doi = self.normalise(doi_full)
            if doi is not None:
                tentative = 3
                while tentative:
                    tentative -= 1
                    try:
                        r = get(self._api + quote(doi), headers=self._headers, timeout=30)
                        if r.status_code == 200:
                            r.encoding = "utf-8"
                            json_res = loads(r.text)
                            valid_bool = json_res.get("responseCode") == 1
                            if get_extra_info:
                                return valid_bool, self.extra_info(json_res)
                            return valid_bool
                    except ReadTimeout:
                        # Do nothing, just try again
                        pass
                    except ConnectionError:
                        # Sleep 5 seconds, then try again
                        sleep(5)
            else:
                if get_extra_info:
                    return False, {"valid": False}
                return False

        if get_extra_info:
            return False, {"valid": False}
        return False

    def extra_info(self, api_response):
        result = {}
        result["valid"] = True
        # import crossref and datacite resource finder for extra info
        return result
