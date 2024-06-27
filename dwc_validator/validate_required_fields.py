import pandas as pd
from pandas import DataFrame

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