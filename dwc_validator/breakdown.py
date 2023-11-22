"""
Breakdowns are used to generate the breakdowns section of the validation
"""
from typing import Dict
import pandas as pd
from pandas import DataFrame


def generate_breakdowns(dataframe: DataFrame) -> Dict[str, Dict[str, int]]:
    """
    Generate a dictionary of breakdowns
    :param dataframe:
    :return:
    """
    breakdowns = {}

    if 'year' in dataframe.columns:
        breakdowns['year'] = simple_breakdown(dataframe, 'year')
    if 'month' in dataframe.columns:
        breakdowns['month'] = simple_breakdown(dataframe, 'month')
    if 'day' in dataframe.columns:
        breakdowns['day'] = simple_breakdown(dataframe, 'day')
    if 'scientificName' in dataframe.columns:
        breakdowns['scientificName'] = top_values_breakdown(
            dataframe, 'scientificName', 20)
    if 'family' in dataframe.columns:
        breakdowns['family'] = top_values_breakdown(dataframe, 'family', 20)
    if 'eventDate' in dataframe.columns:
        year_group_by, month_group_by, day_group_by = generate_event_date_breakdown(
            dataframe)
        breakdowns['year'] = year_group_by
        breakdowns['month'] = month_group_by
        breakdowns['day'] = day_group_by
    return breakdowns


def field_populated_counts(dataframe: DataFrame) -> Dict[str, int]:
    """
    Generate a dictionary of field names and the number of non-empty values
    :param dataframe:
    :return:
    """
    # Get list of columns
    columns_list = dataframe.columns.tolist()

    # Get count of non-empty values for each column
    non_empty_counts = dataframe.notna().sum()

    # Create a dictionary with column names as keys and non-empty counts as
    # values
    return {column: int(non_empty_counts[column]) for column in columns_list}


def top_values_breakdown(dataframe: DataFrame, field, limit) -> Dict[str, int]:
    """
    Generate a breakdown of the top values for a field
    :param dataframe:
    :param field:
    :param limit:
    :return:
    """
    return dataframe[field].value_counts().head(limit).to_dict()


def simple_breakdown(dataframe: DataFrame, field) -> Dict[str, int]:
    """
    Generate a simple breakdown of a field
    :param dataframe:
    :param field:
    :return:
    """
    return {
        str(key): value for key,
        value in dataframe[field].value_counts().to_dict().items()}


def generate_event_date_breakdown(
        dataframe: DataFrame) -> (Dict[str, int], Dict[str, int], Dict[str, int]):
    """
    Generate a breakdown of the eventDate field
    :param dataframe:
    :return:
    """

    # Parse 'eventDate' field, coerce errors
    dataframe['eventDate'] = pd.to_datetime(dataframe['eventDate'], errors='coerce')

    # Filter out records with valid dates
    valid_records = dataframe.dropna(subset=['eventDate'])

    valid_records['year'] = valid_records['eventDate'].map(lambda x: x.year)
    valid_records['month'] = valid_records['eventDate'].map(lambda x: x.month)
    valid_records['day'] = valid_records['eventDate'].map(lambda x: x.day)

    year_group_by = valid_records['year'].to_frame().groupby(
        by="year").size().to_dict()
    month_group_by = valid_records['month'].to_frame().groupby(
        by="month").size().to_dict()
    day_group_by = valid_records['day'].to_frame().groupby(
        by="day").size().to_dict()

    return year_group_by, month_group_by, day_group_by
