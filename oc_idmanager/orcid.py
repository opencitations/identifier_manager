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
from urllib.parse import quote
from requests import get
from json import loads
from requests import ReadTimeout
from requests.exceptions import ConnectionError
from time import sleep

from oc_idmanager.base import IdentifierManager


class ORCIDManager(IdentifierManager):
    """This class implements an identifier manager for orcid identifier."""

    def __init__(self, data={}, use_api_service=True):
        """Orcid Manager constructor."""
        super(ORCIDManager, self).__init__()
        self._api = "https://pub.orcid.org/v3.0/"
        self._use_api_service = use_api_service
        self._p = "orcid:"
        self._data = data

    def is_valid(self, id_string):
        orcid = self.normalise(id_string, include_prefix=True)
        if orcid is None:
            return False
        else:
            if orcid not in self._data or self._data[orcid] is None:
                return (
                    self.syntax_ok(orcid)
                    and self.check_digit(orcid)
                    and self.exists(orcid)
                )
            return self._data[orcid].get("valid")

    def normalise(self, id_string, include_prefix=False):
        try:
            orcid_string = sub("[^X0-9]", "", id_string.upper())
            return "%s%s-%s-%s-%s" % (
                self._p if include_prefix else "",
                orcid_string[:4],
                orcid_string[4:8],
                orcid_string[8:12],
                orcid_string[12:16],
            )
        except:  # Any error in processing the id will return None
            return None

    def check_digit(self, orcid):
        if orcid.startswith(self._p):
            spl = orcid.find(self._p) + len(self._p)
            orcid = orcid[spl:]
        total = 0
        for d in sub("[^X0-9]", "", orcid.upper())[:-1]:
            i = 10 if d == "X" else int(d)
            total = (total + i) * 2
        reminder = total % 11
        result = (12 - reminder) % 11
        return (str(result) == orcid[-1]) or (result == 10 and orcid[-1] == "X")

    def syntax_ok(self, id_string):
        if not id_string.startswith(self._p):
            id_string = self._p+id_string
        return True if match("^orcid:([0-9]{4}-){3}[0-9]{3}[0-9X]$", id_string, re.IGNORECASE) else False


    def exists(self, orcid):
        if self._use_api_service:
            self._headers["Accept"] = "application/json"
            orcid = self.normalise(orcid)
            if orcid is not None:
                tentative = 3
                while tentative:
                    tentative -= 1
                    try:
                        r = get(self._api + quote(orcid), headers=self._headers, timeout=30)
                        if r.status_code == 200:
                            r.encoding = "utf-8"
                            json_res = loads(r.text)
                            return json_res.get("orcid-identifier").get("path") == orcid
                    except ReadTimeout:
                        # Do nothing, just try again
                        pass
                    except ConnectionError:
                        # Sleep 5 seconds, then try again
                        sleep(5)
            else:
                return False
        return False