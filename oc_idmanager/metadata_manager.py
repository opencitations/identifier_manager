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


from oc_meta.plugins.crossref.crossref_processing import CrossrefProcessing
from oc_meta.plugins.datacite.datacite_processing import DataCiteProcessing
from oc_meta.plugins.medra.medra_processing import MedraProcessing
from oc_meta.plugins.jalc.jalc_processing import JalcProcessing
from oc_idmanager.issn import ISSNManager
from oc_idmanager.isbn import ISBNManager
from oc_idmanager.orcid import ORCIDManager
from urllib.parse import quote


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
        if self.metadata_provider is None or self.api_response is None:
            return output_dict
        return eval(f'self.extract_from_{self.metadata_provider}({output_dict})')

    def extract_from_airiti(self, output_dict:dict) -> None:
        pass

    def extract_from_cnki(self, output_dict:dict) -> None:
        pass
    
    def extract_from_crossref(self, output_dict:dict) -> None:
        crossref_processing = CrossrefProcessing()
        output_dict['valid'] = True
        output_dict.update(crossref_processing.csv_creator(self.api_response))
        return output_dict

    def extract_from_datacite(self, output_dict:dict) -> None:
        datacite_processing = DataCiteProcessing()
        output_dict['valid'] = True
        output_dict.update(datacite_processing.csv_creator(self.api_response['data']))
        return output_dict

    def extract_from_jalc(self, output_dict:dict) -> None:
        jalc_processing = JalcProcessing()
        output_dict['valid'] = True
        output_dict.update(jalc_processing.csv_creator(self.api_response))
        return output_dict

    def extract_from_kisti(self, output_dict:dict) -> None:
        pass

    def extract_from_medra(self, output_dict:dict) -> None:
        medra_processing = MedraProcessing()
        output_dict['valid'] = True
        output_dict.update(medra_processing.csv_creator(self.api_response))
        return output_dict

    def extract_from_istic(self, output_dict:dict) -> None:
        pass

    def extract_from_op(self, output_dict:dict) -> None:
        pass

    def extract_from_unknown(self, output_dict:dict) -> None:
        from oc_idmanager.support import call_api, extract_info
        registration_agency = self.api_response[0]['RA'].lower()
        doi = self.api_response[0]['DOI']
        api_registration_agency = getattr(self.doi_manager, f'_api_{registration_agency}')
        if api_registration_agency:
            url = api_registration_agency + quote(doi)
            r_format = 'xml' if registration_agency == 'medra' else 'json'
            extra_api_result = call_api(url=url, headers=self.doi_manager._headers, r_format=r_format)
            return extract_info(extra_api_result, registration_agency, output_dict)