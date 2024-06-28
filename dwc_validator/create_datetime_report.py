from pandas import DataFrame
from .model import DateTimeReport

def create_datetime_report(dataframe: DataFrame):
    """
    Checks if your dates in your dataframe are in valid format (``YYYY-MM-DD`` or ``iso``).

    Parameters
    ----------
        dataframe : `pandas` dataframe
            the data frame to validate

    Returns
    -------
        An object of class `DateTimeReport` that givs information on whether or not your date and times (or ``eventDate``)
        are in the correct format
    """

    # first, check for eventDate
    if 'eventDate' not in dataframe.columns:
        return DateTimeReport(
            has_invalid_datetime=True,
            num_invalid_datetime=dataframe.shape[0]
        )
    
    # initialise the variable to return
    has_invalid_datetime = False
    num_invalid_datetime = 0
    
    # check to see if `eventDate` types are strings, and if they are in YYYY-MM-DD format
    ### TODO: check if they are in iso format???
    datatype_datetime = dataframe.dtypes
    if datatype_datetime['eventDate'] == object:
        datatypes = list(set([type(x) for x in dataframe['eventDate']]))
        if len(datatypes) > 1:
            has_invalid_datetime = True
            num_invalid_datetime = len([x for x in dataframe['eventDate'] if type(x) is str])
        else:
            if datatypes[0] == str:
                for row in dataframe['eventDate']:
                    if 'T' in row:
                        date, time = row.split('T')
                        # check even first
                        event_date = date.split('-')
                        if len(event_date[0]) != 4 or len(event_date[1]) != 2 or len(event_date[2]) != 2:
                            has_invalid_datetime = True
                            num_invalid_datetime += 1
                            continue
                        time_split = time.split(":")
                        if len(time_split[0]) != 2 or len(time_split[1]) != 2 or len(time_split[2]) != 2:
                            has_invalid_datetime = True
                            num_invalid_datetime += 1
                            continue
                    elif '-' in row:
                        event_date = row.split('-')
                        if len(event_date[0]) != 4 or len(event_date[1]) != 2 or len(event_date[2]) != 2:
                            has_invalid_datetime = True
                            num_invalid_datetime += 1
                    
                    else:
                        has_invalid_datetime = True
                        num_invalid_datetime += 1

            else:
                has_invalid_datetime = True
                num_invalid_datetime = dataframe.shape[0]

    # figure out a way to test for iso type
    return {
        "has_invalid_datetime": has_invalid_datetime,
        "num_invalid_datetime": num_invalid_datetime
    }
