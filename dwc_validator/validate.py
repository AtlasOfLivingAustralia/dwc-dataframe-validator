"""
This module contains functions for validating a pandas DataFrame containing Darwin Core data.
"""

import logging
from typing import List
import numpy
import pandas as pd
from pandas import DataFrame
from dwc_validator.breakdown import field_populated_counts
from dwc_validator.model import DFValidationReport, CoordinatesReport, VocabularyReport
from dwc_validator.vocab import basis_of_record_vocabulary, geodetic_datum_vocabulary


def validate_occurrence_dataframe(
        dataframe: DataFrame,
        id_fields: List[str] = None,
        id_term: str = "") -> DFValidationReport:
    """
    Validate a pandas DataFrame containing occurrence data.
    :param dataframe: the data frame to validate
    :param id_fields: fields used to specify a unique identifier for the record
    :param id_term: the actual darwin core term used for the id field e.g. occurrenceID, catalogNumber
    :return:
    """

    errors = []
    warnings = []

    # check id field are fully populated
    record_error_count = check_id_fields(id_fields, id_term, dataframe, errors)

    # check numeric fields have numeric values
    validate_numeric_fields(dataframe, warnings)

    # check taxonomic information supplied - create warning if missing
    valid_taxon_count = validate_required_fields(
        dataframe,
        [
            'scientificName',
            'scientificNameID',
            'taxonID',
            'genus',
            'family',
            'order',
            'class',
            'phylum',
            'kingdom'])

    # check date information supplied - create warning if missing
    valid_temporal_count = validate_required_fields(
        dataframe, ['eventDate', 'year', 'month', 'day'])

    # validate coordinates - create warning if out of range
    coordinates_report = generate_coordinates_report(dataframe, warnings)

    # check recordedBy, recordedByID - create warning if missing
    valid_recorded_by_count = validate_required_fields(
        dataframe, ['recordedBy', 'recordedByID'])

    # check basic compliance with vocabs - basisOfRecord, geodeticDatum, etc.
    vocabs_reports = [
        create_vocabulary_report(
            dataframe,
            "basisOfRecord",
            basis_of_record_vocabulary),
        create_vocabulary_report(
            dataframe,
            "geodeticDatum",
            geodetic_datum_vocabulary)]

    return DFValidationReport(
        record_type="Occurrence",
        record_count=len(dataframe),
        record_error_count=int(record_error_count),
        errors=errors,
        warnings=warnings,
        coordinates_report=coordinates_report,
        records_with_taxonomy_count=int(valid_taxon_count),
        records_with_temporal_count=int(valid_temporal_count),
        records_with_recorded_by_count=int(valid_recorded_by_count),
        column_counts=field_populated_counts(dataframe),
        vocab_reports=vocabs_reports
    )


def validate_event_dataframe(dataframe: DataFrame) -> DFValidationReport:
    """
    Validate a pandas DataFrame containing event data.
    :param dataframe: the data frame to validate
    :return:
    """

    errors = []
    warnings = []

    # check id field are fully populated
    record_error_count = check_id_fields(["eventID"], "", dataframe, errors)

    # check numeric fields have numeric values
    validate_numeric_fields(dataframe, warnings)

    # check date information supplied - create warning if missing
    valid_temporal_count = validate_required_fields(
        dataframe, ['eventDate', 'year', 'month', 'day'])

    # validate coordinates - create warning if out of range
    coordinates_report = generate_coordinates_report(dataframe, warnings)

    # check recordedBy, recordedByID - create warning if missing
    valid_recorded_by_count = validate_required_fields(
        dataframe, ['recordedBy', 'recordedByID'])

    vocabs_reports = [
        create_vocabulary_report(
            dataframe, "geodeticDatum", geodetic_datum_vocabulary)
    ]

    return DFValidationReport(
        record_type="Event",
        record_count=len(dataframe),
        record_error_count=int(record_error_count),
        errors=errors,
        warnings=warnings,
        coordinates_report=coordinates_report,
        records_with_taxonomy_count=0,
        records_with_temporal_count=int(valid_temporal_count),
        records_with_recorded_by_count=int(valid_recorded_by_count),
        column_counts=field_populated_counts(dataframe),
        vocab_reports=vocabs_reports
    )


def validate_required_fields(dataframe: DataFrame, required_fields) -> int:
    """
    Count the number of records with at least one of the required fields populated.

    Parameters:
    - df: pandas DataFrame

    Returns:
    - Count of records with at least one of the required fields populated.
    """
    # Check if all required fields are present in the DataFrame
    if not any(field in dataframe.columns for field in required_fields):
        logging.error("Error: One or more required fields are missing.")
        return 0

    present_fields = filter(lambda x: x in dataframe.columns, required_fields)

    # Count the number of records with at least one of the required fields
    # populated
    at_least_one_populated_count = dataframe[present_fields].notnull().any(
        axis=1).sum()

    # Print the count and return it
    logging.info(
        "Count of records with at least one of the required fields populated: %s", at_least_one_populated_count)
    return at_least_one_populated_count


def generate_coordinates_report(
        dataframe: DataFrame,
        warnings: List[str]) -> CoordinatesReport:
    """
    Validate 'decimalLatitude' and 'decimalLongitude' columns in a pandas DataFrame.

    Parameters:
    - dataframe: pandas DataFrame

    Returns:
    - True if all values are valid, False otherwise.
    """
    # Check if 'decimalLatitude' and 'decimalLongitude' columns exist
    if 'decimalLatitude' not in dataframe.columns or 'decimalLongitude' not in dataframe.columns:
        logging.error(
            "Error: 'decimalLatitude' or 'decimalLongitude' columns not found.")
        return CoordinatesReport(False, 0, 0)

    # get a count of fields populated
    lat_column_non_empty_count = dataframe['decimalLatitude'].count()
    lon_column_non_empty_count = dataframe['decimalLongitude'].count()

    # get a count of fields populated with valid numeric values
    lat_column = pd.to_numeric(dataframe['decimalLatitude'], errors='coerce')
    lon_column = pd.to_numeric(dataframe['decimalLongitude'], errors='coerce')

    # check if all values are valid
    lat_valid_count = lat_column.astype(
        float).between(-90, 90, inclusive='both').sum()
    lon_valid_count = lon_column.astype(
        float).between(-180, 180, inclusive='both').sum()

    if lat_valid_count == lat_column_non_empty_count and lon_valid_count == lon_column_non_empty_count:
        logging.info("All supplied coordinate values are valid.")
        return CoordinatesReport(
            True,
            0, 0)

    logging.error("Error: Some values are not valid.")
    warnings.append("INVALID_OR_OUT_OF_RANGE_COORDINATES")
    return CoordinatesReport(
        True,
        int(lat_column_non_empty_count - lat_valid_count),
        int(lon_column_non_empty_count - lon_valid_count)
    )


def check_id_fields(
        id_fields: List[str],
        id_term: str,
        dataframe: DataFrame,
        errors: List[str]) -> int:
    """
    Check that the id fields are populated for all rows and that the values are unique.
    :param id_fields: the fields used to specify a unique identifier for the record
    :param id_term: the actual darwin core term used for the id field e.g. occurrenceID, catalogNumber
    :param dataframe: the data frame to validate
    :param errors: the list of errors to append to
    :return: records that are missing an id field
    """

    if not id_fields:
        return 0

    for field in id_fields:

        if id_term == field:
            id_field_series = dataframe['id']
        elif field in dataframe.columns:
            id_field_series = dataframe[field]
        else:
            errors.append("MISSING_ID_FIELD")
            logging.error(
                "The %s field is not present in the core file.", field)
            return len(dataframe)

        if id_field_series.notnull().all():
            logging.info("The occurrenceID field is populated for all rows.")

            if len(id_fields) == 1:
                if id_field_series.nunique() == dataframe.shape[0]:
                    logging.info(
                        "The %s has unique values for all rows.", field)
                else:
                    errors.append("DUPLICATE_ID_FIELD_VALUES")
                    logging.error(
                        "The %s field does not have unique values for all rows.", field)
                    return id_field_series.duplicated().sum()
        else:
            errors.append("MISSING_ID_FIELD_VALUES")
            logging.error("The %s field is not populated for all rows.", field)
            return id_field_series.isna().sum()

    return 0


def create_vocabulary_report(
        dataframe: DataFrame,
        field: str,
        controlled_vocabulary: List[str]) -> VocabularyReport:
    """
    Count the number of records with a case-insensitive value in the specified field matching a controlled vocabulary.

    Parameters:
    - dataframe: pandas DataFrame
    - field: str, the field/column in the DataFrame to check
    - controlled_vocabulary: list or set, the controlled vocabulary to compare against

    Returns:
    - Count of records with a case-insensitive value in the specified field matching the controlled vocabulary.
    """
    # Check if the specified field is present in the DataFrame
    if field not in dataframe.columns:
        logging.error("Error: Field '%s' not found in the DataFrame.", field)
        return VocabularyReport(field, False, 0, 0, [])

    # Convert both field values and controlled vocabulary to lowercase (or
    # uppercase)
    not_populated_count = dataframe[field].isna().sum()
    populated_values = dataframe[field].dropna()
    non_matching = []
    matching_records_count = 0

    if len(populated_values) > 0:
        field_values_lower = populated_values.str.lower()
        controlled_vocabulary_lower = set(
            value.lower() for value in controlled_vocabulary)

        # Count the number of records with a case-insensitive value in the
        # specified field matching the controlled vocabulary
        matching_records_count = field_values_lower.isin(
            controlled_vocabulary_lower).sum()

        # pylint: disable=broad-exception-caught
        try:
            x = dataframe.loc[~dataframe[field].str.lower().isin(controlled_vocabulary_lower)][field].to_numpy()
            non_matching = numpy.unique(x.astype(numpy.str_))[:10].tolist()
            if 'nan' in non_matching:
                non_matching.remove('nan')
        except Exception as e:
            logging.error("Error with getting non matching values %s", e, exc_info=True)
            non_matching = []

    # Print the count and return it
    logging.info(
        "Count of records with a case-insensitive value in '%s' "
        "matching the controlled vocabulary: %s", field, matching_records_count)
    return VocabularyReport(
        field=field,
        has_field=True,
        recognised_count=int(matching_records_count),
        unrecognised_count=int(len(dataframe) - (not_populated_count + matching_records_count)),
        non_matching_values=non_matching
    )


def validate_numeric_fields(dataframe: DataFrame, warnings: List[str]):
    """
    Check that the numeric fields have numeric values.
    :param dataframe: the data frame to validate
    :param warnings: the list of warnings to append to
    :return: the list of warnings
    """
    numeric_fields = [
        'decimalLatitude',
        'decimalLongitude',
        'coordinateUncertaintyInMeters',
        'coordinatePrecision',
        'elevation',
        'depth',
        'minimumDepthInMeters',
        'maximumDepthInMeters',
        'minimumDistanceAboveSurfaceInMeters',
        'maximumDistanceAboveSurfaceInMeters',
        'individualCount',
        'organismQuantity',
        'organismSize',
        'sampleSizeValue',
        'temperatureInCelsius',
        'organismAge',
        'year',
        'month',
        'day',
        'startDayOfYear',
        'endDayOfYear']

    for field in numeric_fields:
        if field in dataframe.columns:

            numeric_test = pd.to_numeric(dataframe[field], errors='coerce')

            # Check if the values are either numeric or NaN (for empty strings)
            is_numeric_or_empty = numeric_test.apply(lambda x: pd.isna(x) or pd.api.types.is_numeric_dtype(
                x) or pd.api.types.is_float(x) or pd.api.types.is_integer(x))

            # Return True if all values are numeric or empty, False otherwise
            is_valid = is_numeric_or_empty.all()

            if not is_valid:
                logging.error(
                    "Non-numeric values found in field: %s", field)
                warnings.append(f"NON_NUMERIC_VALUES_IN_{field.upper()}")

    return warnings
