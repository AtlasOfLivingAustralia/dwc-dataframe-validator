"""
Exceptions for the validator.
"""


class ValidationException(Exception):
    """There was a problem validating the data in the DwC-A."""


class CoordinatesException(Exception):
    """There was a problem validating the decimalLatitude, decimalLongitude in the DwC-A."""
