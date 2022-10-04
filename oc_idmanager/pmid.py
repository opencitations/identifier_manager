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
from requests import ReadTimeout
from requests.exceptions import ConnectionError
from time import sleep
from bs4 import BeautifulSoup
from oc_idmanager.base import IdentifierManager
from oc_idmanager.issn import ISSNManager
from datetime import datetime



class PMIDManager(IdentifierManager):
    """This class implements an identifier manager for pmid identifier"""

    def __init__(self, data={}, use_api_service=True):
        """PMID manager constructor."""
        super(PMIDManager,self).__init__()
        self._api = "https://pubmed.ncbi.nlm.nih.gov/"
        self._use_api_service = use_api_service
        self._p = "pmid:"
        self._data = data
        self._im = ISSNManager()

    def is_valid(self, pmid, get_extra_info=False):
        pmid = self.normalise(pmid, include_prefix=True)

        if pmid is None:
            return False
        else:
            if pmid not in self._data or self._data[pmid] is None:
                if get_extra_info:
                    info = self.exists(pmid, get_extra_info=True)
                    self._data[pmid] = info[1]
                    return (info[0] and self.syntax_ok(pmid)), info[1]
                self._data[pmid] = dict()
                self._data[pmid]["valid"] = True if (self.exists(pmid) and self.syntax_ok(pmid)) else False
                return self._data[pmid].get("valid")

            if get_extra_info:
                return self._data[pmid].get("valid"), self._data[pmid]
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


    def exists(self, pmid_full, get_extra_info=False):
        if self._use_api_service:
            pmid = self.normalise(pmid_full)
            if pmid is not None:
                tentative = 3
                while tentative:
                    tentative -= 1
                    try:
                        r = get(
                            self._api + quote(pmid) + "/?format=pubmed",
                            headers=self._headers,
                            timeout=30,
                        )
                        if r.status_code == 200:
                            r.encoding = "utf-8"
                            soup = BeautifulSoup(r.text, features="lxml")
                            txt_obj = str(soup.find(id="article-details"))
                            match_pmid = re.findall("PMID-\s*[1-9]\d*", txt_obj)
                            if match_pmid:
                                if get_extra_info:
                                    return True, self.extra_info(txt_obj)
                                return True
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
            return True, {"valid": True}
        return True

    def extra_info(self, api_response):
        result = {}
        result["valid"] = True

        try:
            title = ""
            fa_title = re.findall("[^BV]TI\s*-\s*([\S\s]*?)\n[A-Z]{2,5}\s*-\s*", api_response)
            for i in fa_title:
                t = re.sub("\s+", " ", i)
                norm_title = t.strip()
                if norm_title is not None:
                    title = norm_title
                    break
        except:
            title = ""

        result["title"] = title

        try:
            authors = set()
            fa_aut = re.findall("FAU\s*-\s*.*[^\n]", api_response)
            for i in fa_aut:
                fau = re.search("(?:FAU\s*-\s*)?(.+)(?:\n)?", i).group(1)
                norm_fau = fau.strip()
                if norm_fau is not None:
                    authors.add(norm_fau)
            authorsList = list(authors)
        except:
            authorsList = []

        result["author"] = authorsList

        try:
            date = re.search(
                "DP\s+-\s+(\d{4}(\s?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))?(\s?((3[0-1])|([1-2][0-9])|([0]?[1-9])))?)",
                api_response,
                re.IGNORECASE,
            ).group(1)
            re_search = re.search(
                "(\d{4})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+((3[0-1])|([1-2][0-9])|([0]?[1-9]))",
                date,
                re.IGNORECASE,
            )
            if re_search is not None:
                src = re_search.group(0)
                datetime_object = datetime.strptime(src, "%Y %b %d")
                pmid_date = datetime.strftime(datetime_object, "%Y-%m-%d")
            else:
                re_search = re.search(
                    "(\d{4})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)",
                    date,
                    re.IGNORECASE,
                )
                if re_search is not None:
                    src = re_search.group(0)
                    datetime_object = datetime.strptime(src, "%Y %b")
                    pmid_date = datetime.strftime(datetime_object, "%Y-%m")
                else:
                    re_search = re.search("(\d{4})", date)
                    if re_search is not None:
                        src = re.search("(\d{4})", date).group(0)
                        datetime_object = datetime.strptime(src, "%Y")
                        pmid_date = datetime.strftime(datetime_object, "%Y")
                    else:
                        pmid_date = ""
        except:
            pmid_date = ""
        result["date"] = pmid_date

        try:
            issnset = set()
            fa_issn = re.findall("IS\s+-\s+[0-9]{4}-[0-9]{3}[0-9X]", api_response)
            for i in fa_issn:
                issn = re.search("[0-9]{4}-[0-9]{3}[0-9X]", i).group(0)
                norm_issn = self._im.normalise(issn, include_prefix=True)
                if norm_issn is not None:
                    issnset.add(norm_issn)
            issnlist = list(issnset)
        except:
            issnlist = []

        try:
            jur_title = ""
            fa_jur = re.findall("JT\s*-\s*.*[^\n]", api_response)
            for i in fa_jur:
                jt = re.search("(?:JT\s*-\s*)?(.+)(?:\n)?", i).group(1)
                norm_jour = jt.strip()
                if norm_jour is not None:
                    jur_title = norm_jour
                    break
        except:
            jur_title = ""

        result["venue"] = (f'{jur_title} {[x for x in issnlist]}' if jur_title else str(issnlist).replace(",", "")).replace("'","")

        try:
            volume = ""
            fa_volume = re.findall("VI\s*-\s*.*[^\n]", api_response)
            for i in fa_volume:
                vi = re.search("(?:VI\s*-\s*)?(.+)(?:\n)?", i).group(1)
                norm_volume = vi.strip()
                if norm_volume is not None:
                    volume = norm_volume
                    break
        except:
            volume = ""

        result["volume"] = volume

        try:
            issue = ""
            fa_issue = re.findall("IP\s*-\s*.*[^\n]", api_response)
            for i in fa_issue:
                vi = re.search("(?:IP\s*-\s*)?(.+)(?:\n)?", i).group(1)
                norm_issue = vi.strip()
                if norm_issue is not None:
                    issue = norm_issue
                    break
        except:
            issue = ""

        result["issue"] = issue

        try:
            pag = ""
            fa_pag = re.findall("PG\s*-\s*.*[^\n]", api_response)
            for i in fa_pag:
                pg = re.search("(?:PG\s*-\s*)?(.+)(?:\n)?", i).group(1)
                norm_pag = pg.strip()
                if norm_pag is not None:
                    pag = norm_pag
                    break
        except:
            pag = ""

        result["page"] = pag

        try:
            pub_types = set()
            types = re.findall("PT\s*-\s*.*[^\n]", api_response)
            for i in types:
                ty = re.search("(?:PT\s*-\s*)?(.+)(?:\n)?", i).group(1)
                norm_type = ty.strip().lower()
                if norm_type is not None:
                    pub_types.add(norm_type)
            typeslist = list(pub_types)
        except:
            typeslist = []

        result["types"] = typeslist

        try:
            publisher = set()
            publishers = re.findall("PB\s*-\s*.*[^\n]", api_response)
            for i in publishers:
                pbs = re.search("(?:PB\s*-\s*)?(.+)(?:\n)?", i).group(1)
                norm_pbs = pbs.strip()
                if norm_pbs is not None:
                    publisher.add(norm_pbs)
            publisherlist = list(publisher)
        except:
            publisherlist = []

        result["publisher"] = publisherlist

        try:
            editor = set()
            editors = re.findall("F*ED\s*-\s*.*[^\n]", api_response)
            for i in editors:
                ed = re.search("(?:F*ED\s*-\s*)?(.+)(?:\n)?", i).group(1)
                norm_ed = ed.strip()
                if norm_ed is not None:
                    editor.add(norm_ed)
            editorlist = list(editor)
        except:
            editorlist = []

        result["editor"] = editorlist

        return result






