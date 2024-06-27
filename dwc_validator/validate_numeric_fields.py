import pandas as pd
from pandas import DataFrame

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