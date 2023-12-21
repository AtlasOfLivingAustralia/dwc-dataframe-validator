"""
This module contains functions for validating a pandas DataFrame containing Darwin Core data.
"""

import logging
from typing import List
import numpy
import requests
import json
import pandas as pd
from pandas import DataFrame
from dwc_validator.breakdown import field_populated_counts
from dwc_validator.model import DFValidationReport, CoordinatesReport, VocabularyReport, TaxonReport
from dwc_validator.vocab import basis_of_record_vocabulary, geodetic_datum_vocabulary, taxon_terms, name_matching_terms

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

    # check for required columns
    all_required_columns_present = False
    missing_columns=[]

    # check for required DwCA terms
    '''
    AB NOTES:
        required fields according to https://support.ala.org.au/support/solutions/articles/6000261427-sharing-a-dataset-with-the-ala
    
        1. Unique record identifier
            - occurrenceID OR catalogNumber OR recordNumber
        2. basisOfRecord
        3. scientificName
        4. eventDate
        5. Location information
            - decimalLatitude AND decimalLongitude AND
              geodeticdatum AND coordinateUncertaintyInMeters
    '''
    ### TODO: refactor below code and write function for this
    if any(map(lambda v: v in ["decimalLatitude", "decimalLongitude", "geodeticDatum","coordinateUncertaintyInMeters"], list(dataframe.columns))):
        validate_required_fields(dataframe, ["basisOfRecord",
                                             "scientificName"
                                             "eventDate",
                                             "basisOfRecord",
                                             "decimalLatitude", 
                                             "decimalLongitude", 
                                             "geodeticDatum",
                                             "coordinateUncertaintyInMeters"])
        check_missing_fields = set(list(dataframe.columns)).issuperset(["decimalLatitude", "decimalLongitude", "geodeticDatum","coordinateUncertaintyInMeters"])
        
        if not check_missing_fields:
            missing_columns = list(set(["decimalLatitude", "decimalLongitude", "geodeticDatum","coordinateUncertaintyInMeters"]).difference(list(dataframe.columns)))
    else:
        validate_required_fields(dataframe, ["basisOfRecord",
                                             "scientificName"
                                             "eventDate"])
        check_missing_fields = list(set(list(dataframe.columns)) - set(["basisOfRecord","scientificName","eventDate"]))
        if type(check_missing_fields) is not bool and len(check_missing_fields) > 0:
            missing_columns = list(set(["basisOfRecord","scientificName","eventDate"]).difference(list(dataframe.columns)))
            missing_columns.append("MAYBE: decimalLatitude")
            missing_columns.append("MAYBE: decimalLongitude")
        
    # check that a unique ID is present for occurrences
    any_present=False
    for entry in ["occurrenceID", "catalogNumber", "recordNumber"]:
        # validate_required_fields(dataframe, [entry])
        check_missing_fields = set(list(dataframe.columns)).issuperset([entry])
        if check_missing_fields:
            any_present=True
            break
    
    # let user know that not of these are present
    if not any_present:
        missing_columns.append("occurrenceID OR catalogNumber OR recordNumber")
        
    # if ids of occurrences are present and all DwCA terms present,
    # set this to True
    if len(missing_columns) == 0:
        all_required_columns_present = True

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
            basis_of_record_vocabulary)
    ]
    if ["geodeticDatum"] in list(dataframe.columns):
        vocabs_reports.append(
            create_vocabulary_report(
            dataframe,
            "geodeticDatum",
            geodetic_datum_vocabulary)
        )

    if "scientificName" in list(dataframe.columns):
        # is this vocabs_reports or is this a separate thing?
        taxonomy_report = create_taxonomy_report(
            dataframe=dataframe
        )
    else:
        taxonomy_report = None

    ### TODO: add number of missing required DwCA columns and list of which are missing
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
        taxonomy_report = taxonomy_report,
        column_counts=field_populated_counts(dataframe),
        vocab_reports=vocabs_reports,
        all_required_columns_present=all_required_columns_present,
        missing_columns=missing_columns,
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

def create_taxonomy_report(dataframe: DataFrame,
                           num_matches: int = 5,
                           include_synonyms: bool = True,
                           change_names_to_backbone: bool = True
                           ) -> TaxonReport:
    """
    Check if taxon is valid for chosen backbone
    """
    ### TODO: add configuration for atlas later
    # check for scientificName, as users should check that they have the correct column names
    if "scientificName" not in list(dataframe.columns):
        raise ValueError("Before checking species names, ensure all your column names comply to DwCA standard.  scientificName is the correct title for species")
    
    # make a list of all scientific names in the dataframe
    scientific_names_list = list(set(dataframe["scientificName"]))

    # initialise has_invalid_taxa
    has_invalid_taxa=False
    
    # send list of scientific names to ALA to check their validity
    payload = [{"scientificName": name} for name in scientific_names_list]
    response = requests.request("POST","https://api.ala.org.au/namematching/api/searchAllByClassification",data=json.dumps(payload))
    response_json = response.json()
    verification_list = {"scientificName": scientific_names_list, "issues": [None for i in range(len(scientific_names_list))]}
    taxonomy = {name: [None for i in range(len(scientific_names_list))] for name in taxon_terms["Australia"]} # REMOVE THIS LATER
    
    # loop over list of names and ensure we have gotten all the issues - might need to do single name search
    # to ensure we get everything
    for i,item in enumerate(scientific_names_list):
        item_index = next((index for (index, d) in enumerate(response_json) if "scientificName" in d and d["scientificName"] == item), None)
        taxonomy["scientificName"][i] = item
        if item_index is not None:
            verification_list["issues"][i] = response_json[item_index]["issues"]
        else:
            response_single = requests.get("https://api.ala.org.au/namematching/api/search?q={}".format("%20".join(item.split(" "))))
            response_json_single = response_single.json()
            if response_json_single['success']:
                if response_json_single['scientificName'] == item:
                    verification_list["issues"][i] = response_json_single["issues"]
                else:
                    verification_list["issues"][i] = "homonym"
            else:
                verification_list["issues"][i] = response_json_single["issues"]

    # check for homonyms - if there are any, then print them out to the user so the user can disambiguate the names
    df_verification = pd.DataFrame(verification_list)
    df_isnull = df_verification.loc[df_verification['issues'].astype(str).str.contains("homonym",case=False,na=False)]
    list_invalid_taxon = []
    matches = {}
    if not df_isnull.empty:
        has_invalid_taxa=True
        invalid_taxon = df_verification.loc[df_verification['issues'].astype(str).str.contains("homonym",case=False,na=False)]
        matches = {x: [] for x in invalid_taxon['scientificName']}
        for name in invalid_taxon['scientificName']:
            print(name)
            print()
            response = requests.get("https://api.ala.org.au/namematching/api/autocomplete?q={}&max={}&includeSynonyms={}".format("%20".join(name.split(" ")),num_matches,str(include_synonyms).lower()))
            # print(response.text)
            # data = {x: [] for x in name_matching_terms["Australia"]} ## REMOVE WHEN HAVE CAPABILILTY FOR ATLASES
            response_json = response.json()
            list_names = []
            if response_json:
                if "synonymMatch" in response_json[0]:
                    print("if loop")
                    for entry in response_json[0]["synonymMatch"]:
                        print(entry)
                        print()
                        # print(pd.DataFrame(entry))
                        # list_names.append(entry["name"])
                else:
                    for entry in response_json:
                        print(entry[["scientificName","rank"]])
                        print(entry['cl'])
                        print()
                    import sys
                    sys.exit()
                    # for entry in response_json[0]["synonymMatch"]:
                    #     print(entry)
                    #     # print(pd.DataFrame(entry))
                    #     # list_names.append(entry["name"])
            else:
                print(response_json)
                response_single = requests.get("https://api.ala.org.au/namematching/api/search?q={}".format("%20".join(name.split(" "))))
                response_json_single = response_single.json()
                print("else loop")
                print(response_json_single)
                import sys
                sys.exit()
                names_df = pd.DataFrame()
                if response_json_single['success']:
                    for item in name_matching_terms["Australia"]: ## REMOVE WHEN HAVE CAPABILILTY FOR ATLASES
                        if item in response_json_single:
                            data[item].append(response_json_single[item])
                        else:
                            data[item].append(None)
            # import sys
            # sys.exit()
            # names_df = pd.DataFrame(data)
            matches[name] = list_names
        list_invalid_taxon = list(invalid_taxon['scientificName'])

    return TaxonReport(
        has_invalid_taxa = has_invalid_taxa,
        unrecognised_taxa = list_invalid_taxon, 
        suggested_names = matches
        )