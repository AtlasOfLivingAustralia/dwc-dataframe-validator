from typing import List
from pandas import DataFrame
import numpy

def check_id_fields(
        id_fields: List[str],
        dataframe: DataFrame) -> int:
    """
    Check that the unique identifier fields are populated for all rows and that the values are unique.

    Parameters
    -----------
        id_fields : ``list``
            the fields used to specify a unique identifier for the record (either or any of occurrenceID, catalogNumber, recordNumber)
        dataframe: ``pandas.DataFrame``
            the data frame to validate

    Returns
    --------
        An object of class ``int`` specifying the number of records that are missing an id field
    """

    if not id_fields:
        return dataframe.shape[0]

    if any(map(lambda v: v in list(dataframe.columns), id_fields)):
        true_indices = numpy.where(list(map(lambda v: v in list(dataframe.columns), id_fields)))[0]
        if len(true_indices) > 1:
            return dataframe.shape[0]
        else:
            id_field_series = dataframe[id_fields[true_indices[0]]]
            if id_field_series.notnull().all():
                return 0
            else:
                return id_field_series.isna().sum()
    else:
        # add_errors(error="You are missing one of the three id fields: {}".format(", ".join(id_fields)))
        return dataframe.shape[0]
