import pandas as pd
from pandas import DataFrame
from .check_for_required_columns import check_for_required_columns
from .check_id_fields import check_id_fields
from .model import EventValidationReport
from .vocab import required_columns_event

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

    # declare variable for required columns presence
    all_required_columns_present = False

    # check eventID field is fully populated
    record_error_count = check_id_fields(id_fields = ["eventID"], dataframe=dataframe)

    # check for required columns
    missing_columns = check_for_required_columns(dataframe=dataframe,required_list=required_columns_event)
    
    # check if there are any missing columns and assign boolean as appropriate
    if len(missing_columns) == 0:
        all_required_columns_present = True

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
