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

    @abstractmethod
    def is_valid(self, id_string):
        """Returns true if the id is valid, false otherwise.

        Args:
            id_string (str): id to check
        Returns:
            bool: True if the id is valid, false otherwise.
        """
        pass

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

    @abstractmethod
    def check_digit(self, id_string):
        """Returns True, if string format is valid (this does not mean registered).

        Args:
            id_string (str): the id to check

        Returns:
            bool: true if id_string is formally correct (according to the id syntax)
        """
        pass

# @abstractmethod
    def exists(self, id_string):
        """
        Optional Method
        Returns True if the id exists, False otherwise. Not all child class check id existence because of API policies
        Args:
            id_string (str): the id string for the api request
        Returns:
            bool: True if the id exists (is registered), False otherwise.
        """
        pass

