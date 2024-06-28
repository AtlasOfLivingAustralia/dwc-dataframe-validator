import numpy
import logging
from pandas import DataFrame
from typing import List
from .model import VocabularyReport

def create_vocabulary_report(
        dataframe: DataFrame,
        field: str,
        controlled_vocabulary: List[str]) -> dict:
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
    return {
        "field": field,
        "has_field": True,
        "recognised_count": int(matching_records_count),
        "unrecognised_count": int(len(dataframe) - (not_populated_count + matching_records_count)),
        "non_matching_values": non_matching
    }