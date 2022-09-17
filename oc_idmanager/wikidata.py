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

    def is_valid(self, wikidata_id):
        """Check if a wikidata ID is valid.

        Args:
            wikidata_id (str): the wikidata ID to check

        Returns:
            bool: true if the wikidata ID is valid, false otherwise.
        """
        wikidata_id = self.normalise(wikidata_id, include_prefix=True)

        if wikidata_id is None or not self.check_digit(wikidata_id):  #metodo is_valid e check_digits sono la stessa cosa ai fini della validazione, no? ha senso tenerli separati?
            return False
        else:
            if not wikidata_id in self._data or self._data[wikidata_id] is None:
                return self.exists(wikidata_id)  # separa metodo exists: is_valid deve ritornare un boolean
            return self._data[wikidata_id].get("valid")

    def normalise(self, id_string, include_prefix=False):
        """It returns the wikidata ID normalized.

        Args:
            id_string (str): the wikidata ID to normalize.
            include_prefix (bool, optional): indicates if include the prefix. Defaults to False.

        Returns:
            str: the normalized wikidata ID
        """
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

    def check_digit(self, id_string):
        """Returns True, if string format is valid (this does not mean registered).

        Args:
            id_string (str): the wikidata ID string to check

        Returns:
            bool: true if the wikidata_id string is formally correct (according to the wikidata_id syntax)
        """
        if not id_string.startswith("wikidata:"):
            id_string = "wikidata:"+id_string
        return True if match("^wikidata:Q[1-9]\\d*$", id_string) else False

    def exists(self, wikidata_id_full):
        """
        Returns True if the wikidata_id exists, False otherwise.
        Args:
            wikidata_id_full (str): the wikidata_id string for the api request
        Returns:
            bool: True if the wikidata_id exists (is registered), False otherwise.
        """
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
                            return json_res.get("responseCode") == 1
                    except ReadTimeout:
                        # Do nothing, just try again
                        pass
                    except ConnectionError:
                        # Sleep 5 seconds, then try again
                        sleep(5)
            else:
                return False

        return False
