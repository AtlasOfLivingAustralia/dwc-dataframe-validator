from pandas import DataFrame
from .model import MMValidationReport
from .check_for_required_columns import check_for_required_columns
from .validate_dwc_terms import validate_dwc_terms
from .vocab import required_multimedia_columns_event,required_multimedia_columns_occ
from .breakdown import field_populated_counts

def validate_media_extension(dataframe: DataFrame, data_type: str) -> dict:
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
        return {
            "missing_columns": missing_columns,
            "incorrect_dwc_terms": incorrect_dwc_terms,
            "record_count": len(dataframe),
            "column_counts": field_populated_counts(dataframe=dataframe),
            "all_required_columns_present": all_required_columns_present
        }
    
    else:
        raise ValueError("Please provide either \"event\" or \"occurrence\" for your data type.")