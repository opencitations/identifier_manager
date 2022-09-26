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


from abc import ABCMeta, abstractmethod


class IdentifierManager(metaclass=ABCMeta):
    """This is the interface that must be implemented by any identifier manager
    for a particular identifier scheme. It provides the signatures of the methods
    for checking the validity of an identifier and for normalising it."""

    def __init__(self, **params):
        """Identifier manager constructor."""
        for key in params:
            setattr(self, key, params[key])

        self._headers = {
            "User-Agent": "Identifier Manager / OpenCitations Indexes "
            "(http://opencitations.net; mailto:contact@opencitations.net)"
        }

    def is_valid(self, id_string, get_extra_info=False):
        """Returns true if the id is valid, false otherwise.

        Args:
            id_string (str): id to check
            get_extra_info (bool, optional): True to get a dictionary with additional info about the id
        Returns:
            bool: True if the id is valid, False otherwise.
            dict : a dictionary with additional information, if required (get_extra_info=True)

        """
        return True

    @abstractmethod
    def normalise(self, id_string, include_prefix=False):
        """Returns the id normalized.

        Args:
            id_string (str): the id to normalize
            include_prefix (bool, optional): indicates if include the prefix. Defaults to False.
        Returns:
            str: normalized id
        """
        pass

    def check_digit(self, id_string):
        """Returns True, if the check digit on the id_string passes (this does not mean that the id is also registered).
        Not all id types have a check digit

        Args:
            id_string (str): the id to check
        Returns:
            bool: true if id_string passes the check digit of the specific id type
        """
        return True

    def syntax_ok(self, id_string):
        """  Returns True if the syntax of the id string is correct, False otherwise.

        Args:
            id_string (str): the id string to check
        Returns:
            bool: True if the id syntax is correct, False otherwise.
        """
        return True

    def exists(self, id_string, get_extra_info=False):
        """  Returns True if the id exists, False otherwise.
        Not all child classes check id existence because of API policies

        Args:
            id_string (str): the id string for the api request
            get_extra_info (bool, optional): True to get a dictionary with additional info about the id

        Returns:
            bool: True if the id exists (is registered), False otherwise.
            dict : a dictionary with additional information, if required
        """
        return True

    def extra_info(self, api_response):
        """  Returns a dictionary with extra info about the id, if available.
        Not all child classes check id existence because of API policies

        Args:
            api_response (json or string): the api response of the api request
        Returns:
            dict: A dictionary with additional information about the id, if provided by the API.
        """
        return {"value": True}
