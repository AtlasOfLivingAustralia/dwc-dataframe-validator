import pandas as pd
from pandas import DataFrame

def validate_dwc_terms(dataframe: DataFrame) -> list:
    """
    Checks if your column names are all valid Darwin Core terms

    Parameters
    ----------
        dataframe : `pandas` dataframe
            the data frame to validate

    Returns
    -------
        ``list`` containing any column names that are invalid Darwin Core terms.  If all are correct, 
        it will return an empty list.
    """

    # get list of potential DwC terms from dataframe
    potential_terms = dataframe.columns

    # missing columns
    incorrect_dwc_terms = []

    dwc_terms = pd.read_csv("https://raw.githubusercontent.com/tdwg/rs.tdwg.org/master/terms-versions/terms-versions.csv")
    dwc_terms_recommended = dwc_terms[dwc_terms["version_status"] == "recommended"].reset_index(drop=True)
    list_terms_recommended = list(dwc_terms_recommended["term_localName"])

    # any(map(lambda v: v in required_taxonomy_columns, list(dataframe.columns))):
    if any(map(lambda v: v not in list_terms_recommended, potential_terms)):
        
        check_missing_fields = set(list_terms_recommended).issuperset(potential_terms)
        
        # check for any missing required fields
        if (not check_missing_fields) or (type(check_missing_fields) is not bool and len(check_missing_fields) > 0):
            if incorrect_dwc_terms is not None:
                missing = list(set(dataframe.columns).difference(set(list_terms_recommended)))
                for entry in missing:
                    incorrect_dwc_terms.append(entry)
            else:
                incorrect_dwc_terms = list(set(dataframe.columns).difference(set(list_terms_recommended)))      

    return incorrect_dwc_terms