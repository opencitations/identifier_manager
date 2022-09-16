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


from oc_id_manager.base import IdentifierManager
from re import sub


class ISBNManager(IdentifierManager):
    """This class implements an identifier manager for isbn identifier"""
    def __init__(self):
        self.p = "isbn:"
        super(ISBNManager, self).__init__()

    def is_valid(self, id_string):
        """It returns the validity of an isbn.

        Args:
            id_string (str): the isbn to validate

        Returns:
            bool: true if the isbn is valid, false otherwise.
        """
        isbn = self.normalise(id_string)
        if (isbn is not None and self.check_digit(isbn)):
            return True

    def normalise(self, id_string, include_prefix=False):
        """It normalizes the ISBN.

        Args:
            id_string (str): the isbn to normalize.
            include_prefix (bool, optional): indicates if include the prefix. Defaults to False.

        Returns:
            str: the normalized isbn
        """
        try:
            isbn_string = sub("[^X0-9]", "", id_string.upper())
            return "%s%s" % (self.p if include_prefix else "", isbn_string)
        except:  # Any error in processing the ISBN will return None
            return None

    def check_digit(self, isbn):
        """Returns True, if ISBN (of length 13 or 10) is valid (this does not mean registered).

        Args:
            isbn (str): the isbn to check

        Raises:
            ValueError: if the len of isbn is not 10 or 13

        Returns:
            bool: true if issn is valid
        """
        isbn = isbn.replace("-", "")
        check_digit = False
        if len(isbn) == 13:
            total = 0
            val = 1
            for x in isbn:
                if x == "X":
                    x = 10
                total += int(x)*val
                val = 3 if val == 1 else val == 1
            if (total % 10) == 0:
                check_digit = True
        elif len(isbn) == 10:
            total = 0
            val = 10
            for x in isbn:
                if x == "X":
                    x = 10
                total += int(x)*val
                val -= 1
            if (total % 11) == 0:
                check_digit = True

        return check_digit