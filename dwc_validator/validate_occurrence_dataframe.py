from pandas import DataFrame
from typing import List
from .model import DFValidationReport
from .vocab import unique_id_vocab,required_taxonomy_columns,required_columns_spatial_vocab,required_columns_other_occ
from .vocab import basis_of_record_vocabulary,geodetic_datum_vocabulary
from .check_for_required_columns import check_for_required_columns
from .create_taxonomy_report import create_taxonomy_report
from .validate_dwc_terms import validate_dwc_terms
from .check_id_fields import check_id_fields
from .validate_dwc_terms import validate_dwc_terms
from .validate_numeric_fields import validate_numeric_fields
from .validate_required_fields import validate_required_fields
from .generate_coordinates_report import generate_coordinates_report
from .create_datetime_report import create_datetime_report
from .create_vocabulary_report import create_vocabulary_report
from .breakdown import field_populated_counts

def validate_occurrence_dataframe(
        dataframe: DataFrame,
        id_fields: List[str] = unique_id_vocab) -> dict:
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
    return {
        "record_type": "Occurrence",
        "record_count": str(len(dataframe)),
        "record_error_count": str(record_error_count),
        "all_required_columns_present": all_required_columns_present,
        "missing_columns": missing_columns,
        "column_counts": field_populated_counts(dataframe),
        "records_with_temporal_count": str(valid_temporal_count['eventDate']),
        # "coordinates_report": coordinates_report,
        # "taxonomy_report": taxonomy_report,
        # "vocab_reports": vocabs_reports,
        # "datetime_report": datetime_report,
        # "incorrect_dwc_terms": incorrect_dwc_terms
    }