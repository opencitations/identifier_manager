#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2022 Arcangelo Massari <arcangelo.massari@unibo.it>
#
# Permission to use, copy, modify, and/or distribute this software for any purpose
# with or without fee is hereby granted, provided that the above copyright notice
# and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND
# FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT,
# OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE,
# DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS
# SOFTWARE.


from oc_idmanager.issn import ISSNManager
from oc_idmanager.orcid import ORCIDManager
from oc_meta.lib.csvmanager import CSVManager
import unicodedata


class JalcProcessing:
    def __init__(self, orcid_index:str=None, doi_csv:str=None):
        self.doi_set = CSVManager.load_csv_column_as_set(doi_csv, 'id') if doi_csv else None
        orcid_index = orcid_index if orcid_index else None
        self.orcid_index = CSVManager(orcid_index)
        self._issnm = ISSNManager()
        self._om = ORCIDManager()

    def csv_creator(self, item:dict) -> dict:
        data = item['data']
        content_type = data['content_type']
        if content_type == 'JA':
            br_type = 'journal article'
        elif content_type == 'BK':
            br_type = 'book'
        elif content_type == 'RD':
            br_type = 'dataset'
        elif content_type == 'EL':
            br_type = 'other'
        elif content_type == 'GD':
            br_type = 'other'
        publisher = self.get_ja(data['publisher_list'])[0]['publisher_name'] if 'publisher_list' in data else ''
        title = self.get_ja(data['title_list'])[0]['title'] if 'title_list' in data else ''
        authors = list()
        if 'creator_list' in data:
            for creator in data['creator_list']:
                sequence = creator['sequence'] if 'sequence' in creator else ''
                # creator_type = creator['type'] if 'type' in creator else ''
                names = creator['names'] if 'names' in creator else ''
                ja_name = self.get_ja(names)[0]
                last_name = ja_name['last_name'] if 'last_name' in ja_name else ''
                first_name = ja_name['first_name'] if 'first_name' in ja_name else ''
                full_name = ''
                if last_name:
                    full_name += last_name
                    if first_name:
                        full_name += f', {first_name}'
                if full_name:
                    authors.append((sequence, full_name))
        authors = [author[1] for author in sorted(authors, key=lambda x: x[0])]
        pub_date_dict = data['publication_date'] if 'publication_date' in data else ''
        pub_date_list = list()
        year = pub_date_dict['publication_year'] if 'publication_year' in pub_date_dict else ''
        if year:
            pub_date_list.append(year)
            month = pub_date_dict['publication_month'] if 'publication_month' in pub_date_dict else ''
            if month:
                pub_date_list.append(month)
                day = pub_date_dict['publication_day'] if 'publication_day' in pub_date_dict else ''
                if day:
                    pub_date_list.append(day)
        pub_date = '-'.join(pub_date_list)
        if 'journal_title_name_list' in data:
            venue = [item for item in self.get_ja(data['journal_title_name_list']) if item['type'] == 'full'][0]['journal_title_name']
        else:
            venue = ''
        issue = data['issue'] if 'issue' in data else ''
        volume = data['volume'] if 'volume' in data else ''
        first_page = data['first_page'] if 'first_page' in data else ''
        first_page = f'"{first_page}"' if '-' in first_page else first_page
        last_page = data['last_page'] if 'last_page' in data else ''
        last_page = f'"{last_page}"' if '-' in last_page else last_page
        pages = ''
        if first_page:
            pages += first_page
            if last_page:
                pages += f'-{last_page}'
        return {
            'title': unicodedata.normalize('NFKC', title),
            'author': unicodedata.normalize('NFKC', '; '.join(authors)),
            'issue': unicodedata.normalize('NFKC', issue),
            'volume': unicodedata.normalize('NFKC', volume),
            'venue': unicodedata.normalize('NFKC', venue),
            'pub_date': unicodedata.normalize('NFKC', pub_date),
            'pages': unicodedata.normalize('NFKC', pages),
            'type': unicodedata.normalize('NFKC', br_type),
            'publisher': unicodedata.normalize('NFKC', publisher),
            'editor': unicodedata.normalize('NFKC', '')
        }
    
    @classmethod
    def get_ja(cls, field:list) -> list:
        return [item for item in field if item['lang'] == 'ja']
