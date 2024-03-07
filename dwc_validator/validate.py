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
from dwc_validator.model import MMValidationReport,EMOFValidationReport,DateTimeReport,EventValidationReport
from dwc_validator.vocab import basis_of_record_vocabulary, geodetic_datum_vocabulary, taxon_terms, unique_id_vocab
from dwc_validator.vocab import required_columns_spatial_vocab,required_columns_other_occ,required_emof_columns_event
from dwc_validator.vocab import required_taxonomy_columns,required_multimedia_columns_occ,required_multimedia_columns_event
from dwc_validator.vocab import required_columns_event

def validate_occurrence_dataframe(
        dataframe: DataFrame,
        id_fields: List[str] = unique_id_vocab) -> DFValidationReport:
    """
    Validates a pandas DataFrame containing occurrence data.  It runs the following checks:

    - Checks for columns required by your chosen Atlas; details which ones are missing, if any
    - Checks for column names that are not EventCore compliant
    - Validates any numeric fields you have
    - Checks presence and validity of columns dealing with spatial data
    - Checks for a column denoting unique identifiers for each occurrence
    - Checks whether or not your coordinates are valid
    - Checks that your dates are in the correct format
    - Checks whether values in required columns are valid

    Required fields according to https://support.ala.org.au/support/solutions/articles/6000261427-sharing-a-dataset-with-the-ala

    Parameters
    -----------
        dataframe : ``pandas`` DataFrame
            dataframe to validate for DwC terms
        id_fields : ``list``
            fields used to specify a unique identifier for the record

    Returns
    --------
        An object of type ``DFValidationReport`` that gives you information about your dataframe.  This is partly
        in JSON format and can be parse by the ``galaxias-python`` package
    """

    # initialise variables to check for required columns
    all_required_columns_present = False
    missing_columns=[]

    # initialise variables for taxonomy report
    taxonomy_report = None

    # check for incorrect Darwin Core terms
    incorrect_dwc_terms = validate_dwc_terms(dataframe=dataframe)
    
    # check for missing taxonomic columns
    taxonomy_missing_columns = check_for_required_columns(dataframe=dataframe,required_list=required_taxonomy_columns)

    # add missing columns from taxonomy to missing columns
    if taxonomy_missing_columns is not None:

        # check to see if vernacularName is in missing columns; remove if so as it's not required
        if 'vernacularName' in taxonomy_missing_columns:
            taxonomy_missing_columns.remove('vernacularName')
        for entry in taxonomy_missing_columns:
            missing_columns.append(entry)

    # check for scientificName - if it is there, generate a taxonomy report
    if 'scientificName' in list(dataframe.columns):
        taxonomy_report = create_taxonomy_report(
            dataframe=dataframe
        )
    else:
        taxonomy_report = None

    # check for missing taxonomic columns
    spatial_missing_columns = check_for_required_columns(dataframe=dataframe,required_list=required_columns_spatial_vocab)

    # add missing columns from taxonomy to missing columns
    if spatial_missing_columns is not None:
        for entry in spatial_missing_columns:
            missing_columns.append(entry)

    # check for missing taxonomic columns
    other_missing_columns = check_for_required_columns(dataframe=dataframe,required_list=required_columns_other_occ)

    if 'decimalLatitude' not in missing_columns and 'decimalLatitude' not in dataframe.columns:
        missing_columns.append("MAYBE: decimalLatitude")
        missing_columns.append("MAYBE: decimalLongitude")   

    # add missing columns from taxonomy to missing columns
    if other_missing_columns is not None:
        for entry in other_missing_columns:
            missing_columns.append(entry)

    # check id field are fully populated
    record_error_count = check_id_fields(id_fields = id_fields, dataframe=dataframe)

    # check numeric fields have numeric values; return any warnings from this check
    validate_numeric_fields(dataframe)

    # check that a unique ID is present for occurrences
    any_present=False
    for entry in unique_id_vocab:
        check_missing_fields = set(list(dataframe.columns)).issuperset([entry])
        if check_missing_fields:
            any_present=True
            break
    
    # if no unique ID for each occurrence exists, let user know
    if not any_present:
        if missing_columns is not None:
            missing_columns.append("occurrenceID OR catalogNumber OR recordNumber")
        else:
            missing_columns = ["occurrenceID OR catalogNumber OR recordNumber"]
    
    # if ids of occurrences are present and all DwCA terms present, set this to True
    if len(missing_columns) == 0:
        all_required_columns_present = True

    # check date information supplied - create warning if missing
    valid_temporal_count = validate_required_fields(dataframe, ['eventDate'])
    
    # validate coordinates - create warning if out of range
    coordinates_report = generate_coordinates_report(dataframe)

    # validate datetime column
    datetime_report = create_datetime_report(dataframe)

    # check that there is a valid basisOfRecord, i.e. HumanObservation
    vocabs_reports = [
        create_vocabulary_report(
            dataframe,
            "basisOfRecord",
            basis_of_record_vocabulary)
    ]

    # check that there is a Coordinate Reference System
    if ["geodeticDatum"] in list(dataframe.columns):
        vocabs_reports.append(
            create_vocabulary_report(
            dataframe,
            "geodeticDatum",
            geodetic_datum_vocabulary)
        )

    # return a report on the data frame
    return DFValidationReport(
        record_type="Occurrence",
        record_count=len(dataframe),
        record_error_count=record_error_count,
        all_required_columns_present=all_required_columns_present,
        missing_columns=missing_columns,
        column_counts=field_populated_counts(dataframe),
        records_with_temporal_count=valid_temporal_count['eventDate'], #change this
        coordinates_report=coordinates_report,
        taxonomy_report = taxonomy_report,
        vocab_reports=vocabs_reports,
        datetime_report=datetime_report,
        incorrect_dwc_terms=incorrect_dwc_terms
    )

def validate_event_dataframe(dataframe: DataFrame) -> EventValidationReport:
    """
    Validates a pandas DataFrame containing event data.  It runs the following checks:

    - Checks for columns required by your chosen Atlas; details which ones are missing, if any
    - Checks for column names that are not Darwin Core compliant
    - Validates any numeric fields you have
    - Checks for a column denoting unique identifiers for each occurrence
    - Checks that your dates are in the correct format
    - Checks whether values in required columns are valid

    Parameters
    -----------
        dataframe : ``pandas`` DataFrame
            dataframe to validate for DwC terms

    Returns
    --------
        An object of type ``EventValidationReport`` that gives you information about your dataframe.  This is partly
        in JSON format and can be parse by the ``galaxias-python`` package
    """

    # check eventID field is fully populated
    record_error_count = check_id_fields(id_fields = ["eventID"], dataframe=dataframe)

    # check for required columns
    missing_columns = check_for_required_columns(dataframe=dataframe,required_list=required_columns_event)

    # check if there are any missing columns and assign boolean as appropriate
    if len(missing_columns) > 0:
        all_required_columns_present = True
    else:
        all_required_columns_present = False

    # check for incorrect dwc terms
    incorrect_dwc_terms = validate_dwc_terms(dataframe=dataframe)

    # check numeric fields have numeric values; return any warnings from this check
    validate_numeric_fields(dataframe)

    # check date information supplied - create warning if missing
    valid_temporal_count = validate_required_fields(dataframe, ['eventDate'])

    # create a report on the datetime
    datetime_report = create_datetime_report(dataframe=dataframe)

    return EventValidationReport(
        record_type="Event",
        record_count=len(dataframe),
        record_error_count=int(record_error_count),
        all_required_columns_present=all_required_columns_present,
        missing_columns=missing_columns,
        records_with_temporal_count=int(valid_temporal_count),
        column_counts=field_populated_counts(dataframe),
        datetime_report=datetime_report,
        incorrect_dwc_terms=incorrect_dwc_terms
    )

def validate_media_extension(dataframe: DataFrame, data_type: str) -> MMValidationReport:
    """
    Validates a pandas DataFrame containing multimedia data.  It runs the following checks:

    - Checks for columns required by your chosen Atlas; details which ones are missing, if any
    - Checks for column names that are not EventCore or DarwinCore compliant
    - Checks for a column denoting unique identifiers for each occurrence
    - Checks whether values in required columns are valid

    Parameters
    -----------
        dataframe : ``pandas`` DataFrame
            dataframe to validate for DwC terms
        data_type : ``str``
            type of archive you will be building.  Your choice is between an ``event`` and an ``occurrence``.

    Returns
    --------
        An object of type ``MMValidationReport`` that gives you information about your multimedia dataframe.  
        This is partly in JSON format and can be parsed by the ``galaxias-python`` package
    """
    
    if data_type.lower() == "event" or data_type.lower() == "occurrence":
        
        # check for missing columns
        if data_type.lower() == "event":
            missing_columns = check_for_required_columns(dataframe=dataframe,required_list=required_multimedia_columns_event)
        else:
            missing_columns = check_for_required_columns(dataframe=dataframe,required_list=required_multimedia_columns_occ)

        # check all column names are dwc compliant
        incorrect_dwc_terms = validate_dwc_terms(dataframe=dataframe)

        # check if all required columns are present
        if len(missing_columns) == 0:
            all_required_columns_present = True
        else:
            all_required_columns_present = False

        # return report on multimedia
        return MMValidationReport(
            missing_columns=missing_columns,
            incorrect_dwc_terms = incorrect_dwc_terms,
            record_count=len(dataframe),
            column_counts=field_populated_counts(dataframe=dataframe),
            all_required_columns_present=all_required_columns_present
        )
    
    else:
        raise ValueError("Please provide either \"event\" or \"occurrence\" for your data type.")

def validate_emof_extension(dataframe: DataFrame) -> EMOFValidationReport:
    """
    Validates a pandas DataFrame containing multimedia data.  It runs the following checks:

    - Checks for columns required by your chosen Atlas; details which ones are missing, if any
    - Checks for column names that are not EventCore or DarwinCore compliant
    - Checks for a column denoting unique identifiers for each occurrence
    - Checks whether values in required columns are valid

    Parameters
    -----------
        dataframe : ``pandas`` DataFrame
            dataframe to validate for DwC terms
        
    Returns
    --------
        An object of type ``EMOFValidationReport`` that gives you information about your multimedia dataframe.  
        This is partly in JSON format and can be parsed by the ``galaxias-python`` package
    """

    # first, check for missing columns
    missing_columns = check_for_required_columns(dataframe=dataframe,required_list=required_emof_columns_event)

    # check all column names are dwc compliant
    incorrect_dwc_terms = validate_dwc_terms(dataframe=dataframe)

    # check if all required columns are present
    if len(missing_columns) == 0:
        all_required_columns_present = True
    else:
        all_required_columns_present = False

    return EMOFValidationReport(
        record_count = len(dataframe),
        missing_columns = missing_columns,
        column_counts = field_populated_counts(dataframe=dataframe),
        incorrect_dwc_terms = incorrect_dwc_terms,
        all_required_columns_present=all_required_columns_present
    )

def validate_required_fields(dataframe: DataFrame, required_fields) -> pd.Series:
    """
    Check that all required fields have data in all rows

    Parameters
    -----------
        dataframe : pandas DataFrame
            the dataframe you want to validate
        required_fields : list
            a list of fields required by the DwCA standard and/or the chosen submission atlas

    Returns
    --------
        ``pandas.Series`` denoting how many rows in the dataframe each required column has
    """
    # Check if all required fields are present in the DataFrame
    if not any(field in dataframe.columns for field in required_fields):
        return pd.Series({x: 0 for x in required_fields})

    # check only fields that are reqired
    present_fields = filter(lambda x: x in dataframe.columns, required_fields)

    # get the number of rows containing non-null values
    required_fields_populated_count = dataframe[present_fields].count(axis=0)
    
    # Return count for each column
    return required_fields_populated_count

def check_for_required_columns(dataframe: DataFrame, required_list: list) -> pd.Series:
    """
    Check to see if your dataframe has all of the columns in the required_list

    Parameters
    -----------
        dataframe : pandas DataFrame
            the dataframe you want to validate
        required_list : list
            a list of fields required by the DwCA standard and/or the chosen submission atlas

    Returns
    --------
        ``list`` denoting the missing required columns (empty if they are all present).
    """

    if any(map(lambda v: v in required_list, list(dataframe.columns))):

        # check to see if we are missing any columns
        check_missing_fields = set(list(dataframe.columns)).issuperset(required_list)
        
        # check for any missing required fields
        if (not check_missing_fields) or (type(check_missing_fields) is not bool and len(check_missing_fields) > 0):
            return list(set(required_list).difference(set(dataframe.columns)))
        else:
            return []

def generate_coordinates_report(
        dataframe: DataFrame) -> CoordinatesReport:
    """
    Check that 'decimalLatitude' and 'decimalLongitude' columns are the correct format and between
    -90\N{DEGREE SIGN} and 90\N{DEGREE SIGN} for latitude, and -180\N{DEGREE SIGN} and 180\N{DEGREE SIGN} 
    for longitude.

    Parameters
    -----------
        dataframe: ``pandas`` DataFrame
            the dataframe you are looking to validate

    Returns
    ---------
        An object of type ``CoordinatesReport``
    """
    # Check if 'decimalLatitude' and 'decimalLongitude' columns exist
    if 'decimalLatitude' not in dataframe.columns or 'decimalLongitude' not in dataframe.columns:
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
        return CoordinatesReport(True,0, 0)

    # add to warnings
    # add_warnings("INVALID_OR_OUT_OF_RANGE_COORDINATES")
    return CoordinatesReport(
        True,
        int(lat_column_non_empty_count - lat_valid_count),
        int(lon_column_non_empty_count - lon_valid_count)
    )


def check_id_fields(
        id_fields: List[str],
        dataframe: DataFrame) -> int:
    """
    Check that the unique identifier fields are populated for all rows and that the values are unique.

    Parameters
    -----------
        id_fields : ``list``
            the fields used to specify a unique identifier for the record (either or any of occurrenceID, catalogNumber, recordNumber)
        dataframe: ``pandas.DataFrame``
            the data frame to validate

    Returns
    --------
        An object of class ``int`` specifying the number of records that are missing an id field
    """

    if not id_fields:
        # add_warnings("Please provide id_fields to check_id_fields")
        return dataframe.shape[0]

    if any(map(lambda v: v in list(dataframe.columns), id_fields)):
        true_indices = numpy.where(list(map(lambda v: v in list(dataframe.columns), id_fields)))[0]
        if len(true_indices) > 1:
            # add_errors(error="You have multiple id fields.  Please remove one of the following: {}".format(", ".join(id_fields[true_indices])))
            return dataframe.shape[0]
        else:
            id_field_series = dataframe[id_fields[true_indices[0]]]
            if id_field_series.notnull().all():
                return 0
            else:
                # add_errors("There are missing values in the field {}".format(id_fields[true_indices[0]]))
                return id_field_series.isna().sum()
    else:
        # add_errors(error="You are missing one of the three id fields: {}".format(", ".join(id_fields)))
        return dataframe.shape[0]

def create_vocabulary_report(
        dataframe: DataFrame,
        field: str,
        controlled_vocabulary: List[str]) -> VocabularyReport:
    """
    Count the number of records with a case-insensitive value in the specified field matching a controlled vocabulary.

    Parameters
    -----------
        dataframe : ``pandas`` DataFrame
            dataframe to validate for DwC terms
        field : str
            the field/column in the DataFrame to check
        controlled_vocabulary : list or set
            a list of the controlled vocabulary (in this case DwC terms) to compare against

    Returns
    --------
        Count of records with a case-insensitive value in the specified field matching the controlled vocabulary.
    """

    # Check if the specified field is present in the DataFrame
    if field not in dataframe.columns:
        return VocabularyReport(field, False, 0, 0, [])

    # Convert both field values and controlled vocabulary to lowercase (or uppercase)
    not_populated_count = dataframe[field].isna().sum()
    populated_values = dataframe[field].dropna()
    non_matching = []
    matching_records_count = 0

    # check that the field is actually populated
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

    # Return a vocabulary report on the column
    return VocabularyReport(
        field=field,
        has_field=True,
        recognised_count=int(matching_records_count),
        unrecognised_count=int(len(dataframe) - (not_populated_count + matching_records_count)),
        non_matching_values=non_matching
    )

def validate_numeric_fields(dataframe: DataFrame):
    """
    Check that the numeric fields have numeric values.

    Parameters
    -----------
        dataframe: `pandas` dataFrame 
            the data frame to validate

    Returns
    --------
        ``None``
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
    
    valid_numeric_fields={x: None for x in numeric_fields}

    for field in numeric_fields:
        if field in dataframe.columns:

            # check that we can convert the dataframe to numeric values for a field
            numeric_test = pd.to_numeric(dataframe[field], errors='coerce')

            # Check if the values are either numeric or NaN (for empty strings)
            is_numeric_or_empty = numeric_test.apply(lambda x: pd.isna(x) or pd.api.types.is_numeric_dtype(
                x) or pd.api.types.is_float(x) or pd.api.types.is_integer(x))

            # Return True if all values are numeric or empty, False otherwise
            valid_numeric_fields[field] = is_numeric_or_empty.all()

    return valid_numeric_fields

def create_taxonomy_report(dataframe: DataFrame,
                           num_matches: int = 5,
                           include_synonyms: bool = True,
                           ) -> TaxonReport:
    """
    Check if the given taxon in a data frame are valid for chosen atlas backbone.

    Parameters
    ----------
        dataframe : `pandas` dataframe
            the data frame to validate
        num_matches : int
            the maximum number of possible matches to return when searching for matches in chosen atlas
        include_synonyms : logical
            an option to include any synonyms of the identified taxon in your search

    Returns
    -------
        An object of class `TaxonReport` that givs information on invalid and unrecognised taxa, as well as
        suggested names for taxon that don't match the taxonomic backbone you are checking.
    """
    # check for scientificName, return None if it is not in the column names
    if "scientificName" not in list(dataframe.columns):
        return None
    
    # make a list of all scientific names in the dataframe
    scientific_names_list = list(set(dataframe["scientificName"]))

    # initialise has_invalid_taxa
    has_invalid_taxa=False
    
    # send list of scientific names to ALA to check their validity
    payload = [{"scientificName": name} for name in scientific_names_list]
    response = requests.request("POST","https://api.ala.org.au/namematching/api/searchAllByClassification",data=json.dumps(payload))
    response_json = response.json()
    terms = ["original name"] + ["proposed match(es)"] + ["rank of proposed match(es)"] + taxon_terms["Australia"]
    invalid_taxon_dict = {x: [] for x in terms}
    
    # loop over list of names and ensure we have gotten all the issues - might need to do single name search
    # to ensure we get everything
    for i,item in enumerate(scientific_names_list):
        item_index = next((index for (index, d) in enumerate(response_json) if "scientificName" in d and d["scientificName"] == item), None)
        # taxonomy["scientificName"][i] = item
        if item_index is None:
            # make this better
            has_invalid_taxa = True
            response_single = requests.get("https://api.ala.org.au/namematching/api/autocomplete?q={}&max={}&includeSynonyms={}".format("%20".join(item.split(" ")),num_matches,str(include_synonyms).lower()))
            response_json_single = response_single.json()
            if response_json_single:
                if response_json_single[0]['rank'] is not None:
                    invalid_taxon_dict["original name"].append(item)
                    invalid_taxon_dict["proposed match(es)"].append(response_json_single[0]['name'])
                    invalid_taxon_dict["rank of proposed match(es)"].append(response_json_single[0]['rank'])
                    for term in taxon_terms["Australia"]:
                        if term in response_json_single[0]['cl']:
                            invalid_taxon_dict[term].append(response_json_single[0]['cl'][term])
                        else:
                            invalid_taxon_dict[term].append(None)
                else:

                    # check for synonyms
                    for synonym in response_json_single[0]["synonymMatch"]:
                        if synonym['rank'] is not None:
                            invalid_taxon_dict["original name"].append(item)
                            invalid_taxon_dict["proposed match(es)"].append(synonym['name'])
                            invalid_taxon_dict["rank of proposed match(es)"].append(synonym['rank'])
                            for term in taxon_terms["Australia"]:
                                if term in synonym['cl']:
                                    invalid_taxon_dict[term].append(synonym['cl'][term])
                            else:
                                invalid_taxon_dict[term].append(None)
                        else:
                            print("synonym doesn't match")
            else:

                # try one last time to find a match
                response_search = requests.get("https://api.ala.org.au/namematching/api/search?q={}".format("%20".join(item.split(" "))))
                response_search_json = response_search.json()            
                if response_search_json['success']:
                    invalid_taxon_dict["original name"].append(item)
                    invalid_taxon_dict["proposed match(es)"].append(response_search_json['scientificName'])
                    invalid_taxon_dict["rank of proposed match(es)"].append(response_search_json['rank'])
                    for term in taxon_terms["Australia"]:
                        if term in response_search_json:
                            invalid_taxon_dict[term].append(response_search_json[term])
                        else:
                            invalid_taxon_dict[term].append(None)
                else:
                    print("last ditch search did not work")
                    print(response_search_json)
                    import sys
                    sys.exit()
    
    valid_taxon_count = 999
    if not has_invalid_taxa:
        # now 
        valid_data = validate_required_fields(dataframe,required_taxonomy_columns)
        for entry in valid_data.items():
            if entry[0] != "vernacularName":
                if entry[1] < dataframe.shape[0]:
                    if entry[1] < valid_taxon_count:
                        valid_taxon_count = entry[1]
        if dataframe.shape[0] < valid_taxon_count:
            valid_taxon_count = dataframe.shape[0]
    else:
        valid_taxon_count = 0

    # return report on taxon
    return TaxonReport(
        has_invalid_taxa = has_invalid_taxa,
        unrecognised_taxa = invalid_taxon_dict,
        valid_taxon_count = valid_taxon_count
    )

def create_datetime_report(dataframe: DataFrame):
    """
    Checks if your dates in your dataframe are in valid format (``YYYY-MM-DD`` or ``iso``).

    Parameters
    ----------
        dataframe : `pandas` dataframe
            the data frame to validate

    Returns
    -------
        An object of class `DateTimeReport` that givs information on whether or not your date and times (or ``eventDate``)
        are in the correct format
    """

    # first, check for eventDate
    if 'eventDate' not in dataframe.columns:
        return DateTimeReport(
            has_invalid_datetime=True,
            num_invalid_datetime=dataframe.shape[0]
        )
    
    # initialise the variable to return
    has_invalid_datetime = False
    num_invalid_datetime = 0
    
    # check to see if `eventDate` types are strings, and if they are in YYYY-MM-DD format
    ### TODO: check if they are in iso format???
    datatype_datetime = dataframe.dtypes
    if datatype_datetime['eventDate'] == object:
        datatypes = list(set([type(x) for x in dataframe['eventDate']]))
        if len(datatypes) > 1:
            has_invalid_datetime = True
            num_invalid_datetime = len([x for x in dataframe['eventDate'] if type(x) is str])
        else:
            if datatypes[0] == str:
                for row in dataframe['eventDate']:
                    if '-' in row:
                        event_date = row.split('-')
                        if len(event_date[0]) != 4 or len(event_date[1]) != 2 or len(event_date[2]) != 2:
                            has_invalid_datetime = True
                            num_invalid_datetime += 1
                    else:
                        has_invalid_datetime = True
                        num_invalid_datetime += 1

            else:
                has_invalid_datetime = True
                num_invalid_datetime = dataframe.shape[0]

    # figure out a way to test for iso type
    return DateTimeReport(
        has_invalid_datetime=has_invalid_datetime,
        num_invalid_datetime=num_invalid_datetime
    )

def validate_dwc_terms(dataframe: DataFrame):
    """
    Checks if your column names are all valid Darwin Core terms

    Parameters
    ----------
        dataframe : `pandas` dataframe
            the data frame to validate

    Returns
    -------
        ``list`` containing any column names that are invalid Darwin Core terms.  If all are correct, 
        it will return an empty list.
    """

    # get list of potential DwC terms from dataframe
    potential_terms = dataframe.columns

    # missing columns
    incorrect_dwc_terms = []

    dwc_terms = pd.read_csv("https://raw.githubusercontent.com/tdwg/rs.tdwg.org/master/terms-versions/terms-versions.csv")
    dwc_terms_recommended = dwc_terms[dwc_terms["version_status"] == "recommended"].reset_index(drop=True)
    list_terms_recommended = list(dwc_terms_recommended["term_localName"])

    # any(map(lambda v: v in required_taxonomy_columns, list(dataframe.columns))):
    if any(map(lambda v: v not in list_terms_recommended, potential_terms)):
        
        check_missing_fields = set(list_terms_recommended).issuperset(potential_terms)
        
        # check for any missing required fields
        if (not check_missing_fields) or (type(check_missing_fields) is not bool and len(check_missing_fields) > 0):
            if incorrect_dwc_terms is not None:
                missing = list(set(dataframe.columns).difference(set(list_terms_recommended)))
                for entry in missing:
                    incorrect_dwc_terms.append(entry)
            else:
                incorrect_dwc_terms = list(set(dataframe.columns).difference(set(list_terms_recommended)))      

    return incorrect_dwc_terms