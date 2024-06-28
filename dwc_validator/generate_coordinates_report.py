import pandas as pd
from pandas import DataFrame
from .model import CoordinatesReport

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
    return {
        "has_coordinates_fields": True,
        "invalid_decimal_latitude_count": int(lat_column_non_empty_count - lat_valid_count),
        "invalid_decimal_longitude_count": int(lon_column_non_empty_count - lon_valid_count)
    }