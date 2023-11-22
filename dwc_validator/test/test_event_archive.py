"""
Module: test_event_archive
Description: This module contains test cases for the event archive functionality.
"""

import unittest
import os
from dwca.read import DwCAReader
from dwc_validator import validate_dwca as dwca_validator


def event_data_path(filename):
    """Returns the path to the event archive test data."""
    return os.path.join(os.path.dirname(__file__), 'event_archives', filename)


class EventsTestValidator(unittest.TestCase):
    """Tests the DwCA validator with event archives."""

    def test_validate_ok(self):
        """Tests the DwCA validator with a simple event archive."""
        with DwCAReader(event_data_path("dwca-simple")) as dwca:

            df_validation_report = dwca_validator.validate_archive(dwca)
            self.assertEqual(df_validation_report.core.record_count, 5)
            self.assertEqual(
                df_validation_report.core.coordinates_report.invalid_decimal_latitude_count, 0)
            self.assertEqual(
                df_validation_report.core.coordinates_report.invalid_decimal_longitude_count, 0)
