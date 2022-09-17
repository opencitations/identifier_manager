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
from urllib.parse import quote
from requests import get
from requests import ReadTimeout
from requests.exceptions import ConnectionError
from time import sleep
from bs4 import BeautifulSoup

from oc_idmanager.base import IdentifierManager


class PMIDManager(IdentifierManager):
    """This class implements an identifier manager for pmid identifier"""

    def __init__(self, data={}, use_api_service=True):
        """PMID manager constructor."""
        super(PMIDManager,self).__init__()
        self._api = "https://pubmed.ncbi.nlm.nih.gov/"
        self._use_api_service = use_api_service
        self._p = "pmid:"
        self._data = data

    def is_valid(self, pmid):
        pmid = self.normalise(pmid, include_prefix=True)

        if pmid is None:
            return False
        else:
            if not pmid in self._data or self._data[pmid] is None:
                return self.exists(pmid) and self.syntax_ok(pmid)
            return self._data[pmid].get("valid")

    def normalise(self, id_string, include_prefix=False):
        id_string = str(id_string)
        try:
            pmid_string = sub("^0+", "", sub("\0+", "", (sub("[^\d+]", "", id_string))))
            return "%s%s" % (self._p if include_prefix else "", pmid_string)
        except:
            # Any error in processing the PMID will return None
            return None

    def check_digit(self, id_string):
        if not id_string.startswith(self._p):
            id_string = self._p+id_string
        return True if match("^pmid:[1-9]\d*$", id_string) else False


    def exists(self, pmid_full):
        if self._use_api_service:
            pmid = self.normalise(pmid_full)
            if pmid is not None:
                tentative = 3
                while tentative:
                    tentative -= 1
                    try:
                        r = get(
                            self._api + quote(pmid) + "/?format=pmid",
                            headers=self._headers,
                            timeout=30,
                        )
                        if r.status_code == 200:
                            r.encoding = "utf-8"
                            soup = BeautifulSoup(r.content, features="lxml")
                            for i in soup.find_all("meta", {"name": "uid"}):
                                id = i["content"]
                                if id == pmid:
                                    return True

                    except ReadTimeout:
                        # Do nothing, just try again
                        pass
                    except ConnectionError:
                        # Sleep 5 seconds, then try again
                        sleep(5)
            else:
                return False
        return False
