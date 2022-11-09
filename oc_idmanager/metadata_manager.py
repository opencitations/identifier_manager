#!python
# Copyright 2022, Arianna Moretti <arianna.moretti4@unibo.it>, Arcangelo Massari <arcangelo.massari@unibo.it>
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


from bs4 import BeautifulSoup
from medra_processing import MedraProcessing
from oc_idmanager.issn import ISSNManager
from oc_idmanager.isbn import ISBNManager
from oc_idmanager.orcid import ORCIDManager
from typing import List, Tuple
from urllib.parse import quote
import html
import re


class MetadataManager():
    def __init__(self, metadata_provider:str, api_response:dict):
        self.metadata_provider = metadata_provider
        self.api_response = api_response
        self._issnm = ISSNManager()
        self._isbnm = ISBNManager()
        self._om = ORCIDManager()
        from oc_idmanager.doi import DOIManager
        self.doi_manager = DOIManager()

    def extract_metadata(self, output_dict:dict) -> None:
        if self.metadata_provider is None:
            return output_dict
        return eval(f'self.extract_from_{self.metadata_provider}({output_dict})')
    
    def extract_from_crossref(self, output_dict:dict) -> None:
        api_response_dict = self.api_response
        result = output_dict
        message = api_response_dict["message"]
        if not 'DOI' in message:
            return result
        else:
            if isinstance(message['DOI'], list):
                doi = self.doi_manager.normalise(str(message['DOI'][0]), include_prefix=False)
            else:
                doi = self.doi_manager.normalise(str(message['DOI']), include_prefix=False)

            # GET TITLE
            if result.get("title") is None or result.get("title") ==  "":
                if 'title' in message:
                    if message['title']:
                        if isinstance(message['title'], list):
                            text_title = message['title'][0]
                        else:
                            text_title = message['title']
                        soup = BeautifulSoup(text_title, 'html.parser')
                        title_soup = soup.get_text().replace('\n', '')
                        title = html.unescape(title_soup)
                        result['title'] = title

            # GET AUTHORS and EDITORS
            agents_list = []
            if 'author' in message:
                for author in message['author']:
                    author['role'] = 'author'
                agents_list.extend(message['author'])
            if 'editor' in message:
                for editor in message['editor']:
                    editor['role'] = 'editor'
                agents_list.extend(message['editor'])
            authors_strings_list, editors_string_list = self.get_agents_strings_list(agents_list)

            if result.get("author") is None or result.get("author") == []:
                result["author"] = authors_strings_list
            if result.get("editor") is None or result.get("editor") == []:
                result["editor"] = editors_string_list

            # GET PUB DATE
            if result.get('pub_date') is None or result.get('pub_date') == '':
                if 'issued' in message:
                    if message['issued']['date-parts'][0][0]:
                        result['pub_date'] = '-'.join([str(y) for y in message['issued']['date-parts'][0]])
                    else:
                        result['pub_date'] = ''

            # GET VENUE
            '''
            generation of the venue's name, followed by id in square brackets, separated by spaces.
            HTML tags are deleted and HTML entities escaped. In addition, any ISBN and ISSN are validated.
            Finally, the square brackets in the venue name are replaced by round brackets to avoid conflicts with the ids enclosures.

            'NAME [SCHEMA:ID]', for example, 'Nutrition & Food Science [issn:0034-6659]'. If the id does not exist, the output is only the name. Finally, if there is no venue, the output is an empty string.
            '''
            if result.get("venue") is None or result.get("venue") == "":
                name_and_id = ''
                if 'container-title' in message:
                    if message['container-title']:
                        if isinstance(message['container-title'], list):
                            ventit = str(message['container-title'][0]).replace('\n', '')
                        else:
                            ventit = str(message['container-title']).replace('\n', '')
                        ven_soup = BeautifulSoup(ventit, 'html.parser')
                        ventit = html.unescape(ven_soup.get_text())
                        ambiguous_brackets = re.search('\[\s*((?:[^\s]+:[^\s]+)?(?:\s+[^\s]+:[^\s]+)*)\s*\]', ventit)
                        if ambiguous_brackets:
                            match = ambiguous_brackets.group(1)
                            open_bracket = ventit.find(match) - 1
                            close_bracket = ventit.find(match) + len(match)
                            ventit = ventit[:open_bracket] + '(' + ventit[open_bracket + 1:]
                            ventit = ventit[:close_bracket] + ')' + ventit[close_bracket + 1:]
                        venidlist = list()
                        if 'ISBN' in message:
                            if message['type'] in {'book chapter', 'book part', 'book section', 'book track',
                                                'reference entry'}:
                                self.id_worker(message['ISBN'], venidlist, self.isbn_worker)

                        if 'ISSN' in message:
                            if message['type'] in {'book', 'data file', 'dataset', 'edited book', 'journal article',
                                                'journal volume', 'journal issue', 'monograph', 'proceedings',
                                                'peer review', 'reference book', 'reference entry', 'report'}:
                                self.id_worker(message['ISSN'], venidlist, self.issn_worker)
                            elif message['type'] == 'report series':
                                if 'container-title' in message:
                                    if message['container-title']:
                                        self.id_worker(message['ISSN'], venidlist, self.issn_worker)
                        if venidlist:
                            name_and_id = ventit + ' [' + ' '.join(venidlist) + ']'
                        else:
                            name_and_id = ventit

                result['venue'] = name_and_id

            # GET VOLUME
            if result.get("volume") is None or result.get("volume") == "":
                if 'volume' in message:
                    result['volume'] = message['volume']
                else:
                    result['volume'] = ""

            # GET ISSUE
            if result.get("issue") is None or result.get("issue") == "":
                if 'issue' in message:
                    result['issue'] = message['issue']
                else:
                    result['issue'] = ""


            # GET PAGE
            if result.get("page") is None or result.get("page") == "":
                if 'page' in message:
                    roman_letters = {'I', 'V', 'X', 'L', 'C', 'D', 'M'}
                    pages_list = re.split('[^A-Za-z\d]+(?=[A-Za-z\d]+)', message['page'])
                    clean_pages_list = list()
                    for page in pages_list:
                        # e.g. 583-584
                        if all(c.isdigit() for c in page):
                            clean_pages_list.append(page)
                        # e.g. G27. It is a born digital document. PeerJ uses this approach, where G27 identifies the whole document, since it has no pages.
                        elif len(pages_list) == 1:
                            clean_pages_list.append(page)
                        # e.g. iv-vii. This syntax is used in the prefaces.
                        elif all(c.upper() in roman_letters for c in page):
                            clean_pages_list.append(page)
                        # 583b-584. It is an error. The b must be removed.
                        elif any(c.isdigit() for c in page):
                            page_without_letters = ''.join([c for c in page if c.isdigit()])
                            clean_pages_list.append(page_without_letters)
                    pages = '-'.join(clean_pages_list)
                    result['page'] = pages
                else:
                    result['page'] = ""


            # GET PUBLICATION TYPE
            if result.get("type") is None or result.get("type") == []:
                if 'type' in message:
                    if message['type']:
                        result['type'] = [message['type'].replace('-', ' ')]
                else:
                    result['type'] = []

            # GET PUBLISHERS
            '''
            the aim is to retrieve a string in the format 'NAME [SCHEMA:ID]', for example, 'American Medical Association (AMA) [crossref:10]'. If the id does not exist, the output is only the name. Finally, if there is no publisher, the output is an empty string.
            '''
            if result.get("publisher") is None or result.get("publisher") == []:
                data = {
                    'publisher': '',
                    'member': None,
                    'prefix': doi.split('/')[0]
                }
                for field in {'publisher', 'member'}:
                    if field in message:
                        if message[field]:
                            data[field] = message[field]
                publisher = data['publisher']
                member = data['member']
                name_and_id = f'{publisher} [crossref:{member}]' if member else publisher

                result["publisher"] = [name_and_id]
            else:
                result["publisher"] = []

        return result

    def extract_from_datacite(self, output_dict:dict) -> None:
        result = output_dict
        api_response_dict = self.api_response
        if result.get("valid") is None:
            if "data" in api_response_dict:
                result["valid"] = True
            else:
                result["valid"] = False
                return result

        if result["valid"] is True:
            data = api_response_dict["data"]
            if 'id' not in data or 'type' not in data:
                return result
            elif data['id'] is None or data['id'] == "" or data['type'] != 'dois':
                return result
            try:
                message = data['attributes']
            except:
                return result

            doi = self.doi_manager.normalise(data['id'], include_prefix=False)
            if doi:

                # GET TITLE
                if result.get("title") is None or result.get("title") == "":
                    pub_title = ""
                    if message.get("titles") is not None and message.get("titles")!=[]:
                        for title in message.get("titles"):
                            if title.get("title") is not None:
                                p_title = title.get("title") if title.get("title") is not None else ""
                                soup = BeautifulSoup(p_title, 'html.parser')
                                title_soup = soup.get_text().replace('\n', '')
                                clean_tit = html.unescape(title_soup)
                                pub_title = clean_tit if clean_tit else p_title
                    result['title'] = pub_title

                # GET EDITORS AND AUTHORS

                if result.get("editor") is None or result.get("editor") == [] or result.get("author") is None or result.get("author") == [] :
                    agents_list = []

                    if message.get("contributors") is not None and message.get("contributors") != []:
                        editors = [contributor for contributor in message.get("contributors") if contributor.get("contributorType") == "Editor"]
                        for ed in editors:
                            agent = {}
                            agent["role"] = "editor"
                            agent["name"] = ed.get("name")
                            if ed.get("nameType") == "Personal" or ("familyName" in ed or "givenName" in ed):
                                agent["family"] = ed.get("familyName")
                                agent["given"] = ed.get("givenName")
                                orcid = None
                                if ed.get("nameIdentifiers") is not None and ed.get("nameIdentifiers") != []:
                                    orcid_ids = [x.get("nameIdentifier") for x in ed.get("nameIdentifiers") if x.get("nameIdentifierScheme") == "ORCID"]
                                    orcid = [self._om.normalise(id, include_prefix=True) for id in orcid_ids]
                                agent["orcid"] = orcid
                            agents_list.append(agent)


                    if message.get("creators") is not None and message.get("creators") != []:
                        creators = message.get("creators")
                        for c in creators:
                            agent = {}
                            agent["role"] = "author"
                            agent["name"] = c.get("name")
                            if c.get("nameType") == "Personal" or ("familyName" in c or "givenName" in c):
                                agent["family"] = c.get("familyName")
                                agent["given"] = c.get("givenName")
                                orcid = None
                                if c.get("nameIdentifiers") is not None and c.get("nameIdentifiers") != []:
                                    orcid_ids = [x.get("nameIdentifier") for x in c.get("nameIdentifiers") if
                                                    x.get("nameIdentifierScheme") == "ORCID"]
                                    orcid = [self._om.normalise(id, include_prefix=True) for id in orcid_ids]
                                agent["orcid"] = orcid
                            agents_list.append(agent)

                    authors_strings_list, editors_string_list = self.get_agents_strings_list(agents_list)

                    if result.get("author") is None or result.get("author") == []:
                        result["author"] = authors_strings_list
                    if result.get("editor") is None or result.get("editor") == []:
                        result["editor"] = editors_string_list

                # GET PUB DATE
                if result.get('pub_date') is None or result.get('pub_date') == '':
                    cur_date = ""
                    dates = message.get("dates")
                    if dates:
                        for date in dates:
                            if date.get("dateType") == "Issued":
                                cur_date = date.get("date")
                                break

                    if cur_date == "":
                        if message.get("publicationYear"):
                            cur_date = str(message.get("publicationYear"))

                    result['pub_date'] = cur_date

                # GET VENUE
                '''
                generation of the venue's name, followed by id in square brackets, separated by spaces.
                HTML tags are deleted and HTML entities escaped. In addition, any ISBN and ISSN are validated.
                Finally, the square brackets in the venue name are replaced by round brackets to avoid conflicts with the ids enclosures.

                'NAME [SCHEMA:ID]', for example, 'Nutrition & Food Science [issn:0034-6659]'. If the id does not exist, the output is only the name. Finally, if there is no venue, the output is an empty string.
                '''
                issue = ""
                page = ""
                volume = ""

                if result.get("venue") is None or result.get("venue") == "":
                    cont_title = "unknown_title"
                    is_ids = set()
                    container = message.get("container")
                    if container is not None and container.get("identifierType") == "ISSN" or container.get("identifierType") == "ISBN":

                        cnt_is = container.get("identifier")
                        im = self._issnm if container.get("identifierType") == "ISSN" else self._isbnm
                        norm_is = im.normalise(cnt_is, include_prefix=True)
                        if norm_is is not None:
                            is_ids.add(norm_is)
                        if container.get("issue"):
                            issue = container.get("issue")
                        if container.get("firstPage") and container.get("lastPage") and container.get("lastPage") != "":
                            page = f'{container.get("firstPage")} - {container.get("lastPage")}'
                        elif container.get("firstPage") and (not container.get("lastPage") or container.get("lastPage") == ""):
                            page = f'{container.get("firstPage")}'
                        if container.get("volume"):
                            volume = container.get("volume")

                        if container.get("title"):
                            cont_title = (container["title"].lower()).replace('\n', '')
                            ven_soup = BeautifulSoup(cont_title, 'html.parser')
                            ventit = html.unescape(ven_soup.get_text())
                            ambiguous_brackets = re.search('\[\s*((?:[^\s]+:[^\s]+)?(?:\s+[^\s]+:[^\s]+)*)\s*\]',ventit)
                            if ambiguous_brackets:
                                match = ambiguous_brackets.group(1)
                                open_bracket = ventit.find(match) - 1
                                close_bracket = ventit.find(match) + len(match)
                                ventit = ventit[:open_bracket] + '(' + ventit[open_bracket + 1:]
                                ventit = ventit[:close_bracket] + ')' + ventit[close_bracket + 1:]
                                cont_title = ventit

                    relatedIdentifiers = message.get("relatedIdentifiers")
                    if relatedIdentifiers:
                        for related in relatedIdentifiers:
                            if related.get("relationType"):
                                if related.get("relationType").lower() == "ispartof":
                                    if related.get("relatedIdentifierType"):
                                        relatedIdentifierType = (
                                            str(related["relatedIdentifierType"])
                                        ).lower()
                                        if relatedIdentifierType == "issn" or relatedIdentifierType == "isbn":
                                            im = self._issnm if relatedIdentifierType == "issn" else self._isbnm
                                            if "relatedIdentifier" in related.keys():
                                                relatedIS = im.normalise(str(
                                                    related["relatedIdentifier"]), include_prefix=True
                                                )
                                                if relatedIS:
                                                    is_ids.add(relatedIS)
                                            if issue == "" and related.get("issue"):
                                                issue = related.get("issue")
                                            if page == "" and related.get("firstPage") and related.get(
                                                    "lastPage") and related.get("lastPage") != "":
                                                page = f'{related.get("firstPage")} - {related.get("lastPage")}'
                                            elif page == "" and related.get("firstPage") and (
                                                    not related.get("lastPage") or related.get(
                                                    "lastPage") == ""):
                                                page = f'{related.get("firstPage")}'
                                            if volume == "" and related.get("volume"):
                                                volume = related.get("volume")

                    if len(is_ids)>0:
                        name_and_id = (cont_title + ' [' + ' '.join(list(is_ids)) + ']') if cont_title != "unknown_title" else ' [' + ' '.join(list(is_ids)) + ']'
                    else:
                        name_and_id = cont_title

                    result['venue'] = name_and_id if cont_title != "unknown_title" else ""

                # GET VOLUME
                if result.get("volume") is None or result.get("volume") == "":
                    if volume != "":
                        result['volume'] = volume
                    else:
                        result['volume'] = ""

                # GET ISSUE
                if result.get("issue") is None or result.get("issue") == "":
                    if issue != "":
                        result['issue'] = issue
                    else:
                        result['issue'] = ""


                # GET PAGE
                if result.get("page") is None or result.get("page") == "":
                    if page != "":
                        roman_letters = {'I', 'V', 'X', 'L', 'C', 'D', 'M'}
                        pages_list = re.split('[^A-Za-z\d]+(?=[A-Za-z\d]+)', page)
                        clean_pages_list = list()
                        for pg in pages_list:
                            # e.g. 583-584
                            if all(c.isdigit() for c in pg):
                                clean_pages_list.append(pg)
                            # e.g. G27. It is a born digital document. PeerJ uses this approach, where G27 identifies the whole document, since it has no pages.
                            elif len(pages_list) == 1:
                                clean_pages_list.append(pg)
                            # e.g. iv-vii. This syntax is used in the prefaces.
                            elif all(c.upper() in roman_letters for c in pg):
                                clean_pages_list.append(pg)
                            # 583b-584. It is an error. The b must be removed.
                            elif any(c.isdigit() for c in pg):
                                page_without_letters = ''.join([c for c in pg if c.isdigit()])
                                clean_pages_list.append(page_without_letters)
                        pages = '-'.join(clean_pages_list)
                        result['page'] = pages
                    else:
                        result['page'] = ""

                # GET PUBLICATION TYPE
                if result.get("type") is None or result.get("type") == []:
                    if message.get("types"):
                        result['type'] = [v.replace('-', ' ') for v in message.get("types").values()]
                    else:
                        result['type'] = []

                # GET PUBLISHERS
                '''
                the aim is to retrieve a string in the format 'NAME [SCHEMA:ID]', for example, 'American Medical Association (AMA) [crossref:10]'. If the id does not exist, the output is only the name. Finally, if there is no publisher, the output is an empty string.
                '''
                if result.get("publisher") is None or result.get("publisher") == []:
                    publisher = message.get("publisher")
                    if publisher:
                        publisher = (str(publisher).strip()).replace('\n', '')
                    result["publisher"] = publisher if publisher is not None else ""
                else:
                    result["publisher"] = []
        return result

    def extract_from_medra(self, output_dict:dict) -> None:
        medra_processing = MedraProcessing()
        output_dict['valid'] = True
        output_dict.update(medra_processing.csv_creator(self.api_response))
        return output_dict

    def extract_from_unknown(self, output_dict:dict) -> None:
        from oc_idmanager.support import call_api, extract_info
        registration_agency = self.api_response[0]['RA'].lower()
        doi = self.api_response[0]['DOI']
        api_registration_agency = getattr(self.doi_manager, f'_api_{registration_agency}')
        url = api_registration_agency + quote(doi)
        extra_api_result = call_api(url=url, headers=self.doi_manager._headers)
        return extract_info(extra_api_result, registration_agency, output_dict)
    
    def get_agents_strings_list(self, agents_list:List[dict]) -> Tuple[list, list]:
        authors_strings_list = list()
        editors_string_list = list()
        for agent in agents_list:
            cur_role = agent['role']
            f_name = None
            g_name = None
            agent_string = None
            if 'family' in agent:
                f_name = agent['family']
                if 'given' in agent:
                    g_name = agent['given']
                    agent_string = f_name + ', ' + g_name
                else:
                    agent_string = f_name + ', '
            elif 'name' in agent:
                agent_string = agent['name']
                f_name = agent_string.split()[-1] if ' ' in agent_string else None
            elif 'given' in agent and 'family' not in agent:
                agent_string = ', ' + agent['given']
            orcid = None
            if 'ORCID' in agent:
                if isinstance(agent['ORCID'], list):
                    orcid = str(agent['ORCID'][0])
                else:
                    orcid = str(agent['ORCID'])
            if agent_string and orcid:
                agent_string += ' [' + 'orcid:' + str(orcid) + ']'
            if agent_string:
                if agent['role'] == 'author':
                    authors_strings_list.append(agent_string)
                elif agent['role'] == 'editor':
                    editors_string_list.append(agent_string)
        return authors_strings_list, editors_string_list

    @staticmethod
    def id_worker(field, idlist:list, func) -> None:
        if isinstance(field, list):
            for i in field:
                func(str(i), idlist)
        else:
            id = str(field)
            func(id, idlist)

    @staticmethod
    def issn_worker(issnid, idlist):
        from oc_idmanager import ISSNManager
        issn_manager = ISSNManager()
        issnid = issn_manager.normalise(issnid, include_prefix=False)
        if issn_manager.check_digit(issnid):
            idlist.append('issn:' + issnid)

    @staticmethod
    def isbn_worker(isbnid, idlist):
        from oc_idmanager import ISBNManager
        isbn_manager = ISBNManager()
        isbnid = isbn_manager.normalise(isbnid, include_prefix=False)
        if isbn_manager.check_digit(isbnid):
            idlist.append('isbn:' + isbnid)