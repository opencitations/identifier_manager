#!python
# Copyright 2022, Arcangelo Massari <arcangelo.massari@unibo.it>, Arianna Moretti <arianna.moretti4@unibo.it>
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


from oc_idmanager import DOIManager
import unittest


class MetadataManagerTest(unittest.TestCase):
    def test_extract_from_crossref(self):
        doi_manager = DOIManager(use_api_service=True)
        output = doi_manager.exists(doi_full='10.1007/s11192-022-04367-w', get_extra_info=True, allow_extra_api='crossref')
        expected_output = (
            True, 
            {'valid': True, 
            'title': 'Identifying and correcting invalid citations due to DOI errors in Crossref data', 
            'author': ['Cioffi, Alessia [orcid:http://orcid.org/0000-0002-9812-4065]', 'Coppini, Sara [orcid:http://orcid.org/0000-0002-6279-3830]', 'Massari, Arcangelo [orcid:http://orcid.org/0000-0002-8420-0696]', 'Moretti, Arianna [orcid:http://orcid.org/0000-0001-5486-7070]', 'Peroni, Silvio [orcid:http://orcid.org/0000-0003-0530-4305]', 'Santini, Cristian [orcid:http://orcid.org/0000-0001-7363-6737]', 'Shahidzadeh Asadi, Nooshin [orcid:http://orcid.org/0000-0003-4114-074X]'], 
            'editor': [], 'pub_date': '2022-6', 'page': '3593-3612', 'type': ['journal article'],
            'venue': 'Scientometrics', 'volume': '127', 'issue': '6', 
            'publisher': ['Springer Science and Business Media LLC [crossref:297]']})
        self.assertEqual(output, expected_output)

    def test_extract_from_datacite(self):
        doi_manager = DOIManager(use_api_service=True)
        output = doi_manager.exists(doi_full='10.6084/m9.figshare.1468349', get_extra_info=True, allow_extra_api='datacite')
        expected_output = (
            True, 
            {'valid': True, 
            'title': 'RASH Framework - ESWC 2015 MoM session', 
            'author': ['Peroni, Silvio'], 'editor': [], 'pub_date': '2015', 
            'venue': '', 'volume': '', 'issue': '', 'page': '', 
            'type': ['FIGURE', 'misc', 'graphic', 'ImageObject', 'Poster', 'Image'], 
            'publisher': 'figshare'})
        self.assertEqual(output, expected_output)
