from pandas import DataFrame
from .model import EMOFValidationReport
from .check_for_required_columns import check_for_required_columns
from .validate_dwc_terms import validate_dwc_terms
from .vocab import required_emof_columns_event
from .breakdown import field_populated_counts

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