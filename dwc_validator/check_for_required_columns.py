import pandas as pd
from pandas import DataFrame

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