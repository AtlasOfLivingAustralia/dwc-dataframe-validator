"""
Module: test_event_archive
Description: This module contains test cases for the event archive functionality.
"""

import unittest
import os
from dwca.read import DwCAReader
from dwc_validator import validate_dwca as dwca_validator


def occurrence_data_path(filename):
    """Returns the path to the occurrence archive test data."""
    return os.path.join(
        os.path.dirname(__file__),
        'occurrence_archives',
        filename)


class OccurrenceTestValidator(unittest.TestCase):
    """Tests the DwCA validator with occurrence archives."""

    def test_validate_ok(self):
        """Tests the DwCA validator with a simple occurrence archive."""

        with DwCAReader(occurrence_data_path("dwca-simple")) as dwca:
            df_validation_report = dwca_validator.validate_archive(
                dwca, ["occurrenceID"])
            self.assertEqual(5, df_validation_report.core.record_count)
            self.assertEqual(
                0, df_validation_report.core.coordinates_report.invalid_decimal_latitude_count)
            self.assertEqual(
                0, df_validation_report.core.coordinates_report.invalid_decimal_longitude_count)
            self.assertEqual(
                5, df_validation_report.core.records_with_temporal_count)
            self.assertEqual(
                5, df_validation_report.core.records_with_recorded_by_count)
            self.assertEqual(
                5, df_validation_report.core.records_with_taxonomy_count)

    def test_validate_bad_coordinates(self):
        """Tests the DwCA validator with a simple occurrence archive with bad coordinates."""
        with DwCAReader(occurrence_data_path("dwca-bad-coordinates")) as dwca:
            df_validation_report = dwca_validator.validate_archive(
                dwca, ["occurrenceID"])

            # assert 2 bad coordinates
            self.assertEqual(5, df_validation_report.core.record_count)
            self.assertEqual(
                1, df_validation_report.core.coordinates_report.invalid_decimal_latitude_count)
            self.assertEqual(
                1, df_validation_report.core.coordinates_report.invalid_decimal_longitude_count)

    def test_validate_out_of_range_coordinates(self):
        """Tests the DwCA validator with with out of range coordinates."""
        with DwCAReader(occurrence_data_path("dwca-out-of-range-coordinates")) as dwca:
            df_validation_report = dwca_validator.validate_archive(
                dwca, ["occurrenceID"])

            # assert 2 bad coordinates
            self.assertEqual(5, df_validation_report.core.record_count)
            self.assertEqual(
                1, df_validation_report.core.coordinates_report.invalid_decimal_latitude_count)
            self.assertEqual(
                1, df_validation_report.core.coordinates_report.invalid_decimal_longitude_count)

    def test_validate_geodetic_datum(self):
        """Tests the DwCA validator with a simple occurrence archive with bad geodetic datum."""
        with DwCAReader(occurrence_data_path("dwca-bad-geodetic-datum")) as dwca:
            df_validation_report = dwca_validator.validate_archive(
                dwca, ["occurrenceID"])

            # assert 2 bad coordinates
            self.assertEqual(5, df_validation_report.core.record_count)
            self.assertEqual(
                0, df_validation_report.core.coordinates_report.invalid_decimal_latitude_count)
            self.assertEqual(
                0, df_validation_report.core.coordinates_report.invalid_decimal_longitude_count)

            # get the basis of record report
            geodetic_datum_report = next(
                x for x in df_validation_report.core.vocab_reports if x.field == 'geodeticDatum')
            self.assertEqual(True, geodetic_datum_report.has_field)
            self.assertEqual(4, geodetic_datum_report.recognised_count)
            self.assertEqual(1, geodetic_datum_report.unrecognised_count)

    def test_validate_unrecognised_basis_of_record(self):
        """Tests the DwCA validator with unrecognised basis of record."""
        with DwCAReader(occurrence_data_path("dwca-unrecognised-basis-of-record")) as dwca:
            df_validation_report = dwca_validator.validate_archive(
                dwca, ["occurrenceID"])

            # assert 2 bad coordinates
            self.assertEqual(5, df_validation_report.core.record_count)
            self.assertEqual(
                0, df_validation_report.core.coordinates_report.invalid_decimal_latitude_count)
            self.assertEqual(
                0, df_validation_report.core.coordinates_report.invalid_decimal_longitude_count)

            # get the basis of record report
            basis_of_record_report = next(
                x for x in df_validation_report.core.vocab_reports if x.field == 'basisOfRecord')

            self.assertEqual(True, basis_of_record_report.has_field)
            self.assertEqual(3, basis_of_record_report.recognised_count)
            self.assertEqual(2, basis_of_record_report.unrecognised_count)
            self.assertEqual('NONSENSE', basis_of_record_report.non_matching_values[0])
