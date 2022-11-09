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


from bs4 import BeautifulSoup
from datetime import datetime
from oc_idmanager.issn import ISSNManager
from oc_idmanager.orcid import ORCIDManager
from oc_meta.lib.csvmanager import CSVManager
from typing import List, Tuple


class MedraProcessing:
    def __init__(self, orcid_index:str=None, doi_csv:str=None):
        self.doi_set = CSVManager.load_csv_column_as_set(doi_csv, 'id') if doi_csv else None
        orcid_index = orcid_index if orcid_index else None
        self.orcid_index = CSVManager(orcid_index)
        self._issnm = ISSNManager()
        self._om = ORCIDManager()
    
    def csv_creator(self, xml_soup:BeautifulSoup) -> dict:
        br_type = self.get_br_type(xml_soup)
        return getattr(self, f"extract_from_{br_type.replace(' ', '_')}")(xml_soup)
    
    def extract_from_book(self, xml_soup:BeautifulSoup) -> dict:
        authors, editors = self.get_contributors(xml_soup)
        return {
            'title': self.get_title(xml_soup),
            'author': authors,
            'issue': '',
            'volume': '',
            'venue': '',
            'pub_date': self.get_pub_date(xml_soup),
            'pages': '',
            'type': 'book',
            'publisher': self.get_publisher(xml_soup),
            'editor': editors
        }

    def extract_from_journal_article(self, xml_soup:BeautifulSoup) -> dict:
        serial_publication = xml_soup.find('SerialPublication')
        serial_work = serial_publication.find('SerialWork')
        publisher_name = self.get_publisher(serial_work)
        serial_work_titles:List[BeautifulSoup] = serial_work.findAll('Title')
        for serial_work_title in serial_work_titles:
            if serial_work_title.find('TitleType').get_text() == '01':
                venue_name = serial_work_title.find('TitleText').get_text()
        serial_versions:List[BeautifulSoup] = serial_publication.findAll('SerialVersion')
        venue_ids = list()
        for serial_version in serial_versions:
            if serial_version.find('ProductForm').get_text() in {'JD', 'JB'}:
                issnid = self._issnm.normalise(serial_version.find('IDValue').get_text(), include_prefix=False)
                if self._issnm.check_digit(issnid):
                    venue_ids.append('issn:' + issnid)
        venue = f"{venue_name} [{' '.join(venue_ids)}]"
        journal_issue = xml_soup.find('JournalIssue')
        volume = journal_issue.find('JournalVolumeNumber').get_text()
        issue = journal_issue.find('JournalIssueNumber').get_text()
        content_item = xml_soup.find('ContentItem')
        page_run = content_item.find('PageRun')
        pages = page_run.find('FirstPageNumber').get_text() + '-' + page_run.find('LastPageNumber').get_text()
        authors, editors = self.get_contributors(xml_soup)
        return {
            'title': self.get_title(xml_soup),
            'author': authors,
            'issue': issue,
            'volume': volume,
            'venue': venue,
            'pub_date': self.get_pub_date(content_item),
            'pages': pages,
            'type': 'journal article',
            'publisher': publisher_name,
            'editor': editors
        }

    def get_title(self, context:BeautifulSoup) -> str:
        if context.find('DOISerialArticleWork'):
            content_item = context.find('ContentItem')
            return content_item.find('Title').find('TitleText').get_text()
        elif context.find('DOIMonographicProduct'):
            return context.find('Title').find('TitleText').get_text()
    
    def get_contributors(self, context:BeautifulSoup) -> Tuple[list, list]:
        contributors:List[BeautifulSoup] = context.findAll('Contributor')
        authors = list(); editors = list()
        contributor_roles = {'A01': authors, 'B01': editors}
        for contributor in contributors:
            contributor_role = contributor.find('ContributorRole').get_text()
            person_name_inverted = contributor.find('PersonNameInverted')
            corporate_name = contributor.find('CorporateName')
            author = person_name_inverted.get_text() if person_name_inverted else corporate_name.get_text()
            is_there_name_id = contributor.find('NameIdentifier')
            sequence_number = int(contributor.find('SequenceNumber').get_text())
            if is_there_name_id:
                name_id = self._om.normalise(is_there_name_id.find('IDValue').get_text(), include_prefix=True)
                author += f' [{name_id}]'
            contributor_roles[contributor_role].append((sequence_number, author))
        contributor_roles = {k:[ra[1] for ra in sorted(v, key=lambda x:x[0])] for k,v in contributor_roles.items()}
        return contributor_roles['A01'], contributor_roles['B01']
    
    def get_pub_date(self, context:BeautifulSoup) -> str:
        raw_date = context.find('PublicationDate').get_text()
        try:
            datetime_obj = datetime.strptime(raw_date, '%Y%m%d').strftime('%Y-%m-%d')
        except ValueError:
            try:
                datetime_obj = datetime.strptime(raw_date, '%Y%m').strftime('%Y-%m')
            except ValueError:
                datetime_obj = datetime.strptime(raw_date, '%Y').strftime('%Y')
        return datetime_obj
    
    def get_publisher(self, context:BeautifulSoup) -> str:
        return context.find('Publisher').find('PublisherName').get_text()
    
    @classmethod
    def get_br_type(cls, xml_soup:BeautifulSoup) -> str:
        if xml_soup.find('DOIMonographicProduct'):
            br_type = 'book'
        elif xml_soup.find('DOIMonographicWork'):
            br_type = 'book'
        elif xml_soup.find('DOIMonographChapterWork'):
            br_type = 'book chapter'
        elif xml_soup.find('DOISerialArticleWork'):
            br_type = 'journal article'
        elif xml_soup.find('DOISerialIssueWork'):
            br_type = 'journal issue'
        return br_type