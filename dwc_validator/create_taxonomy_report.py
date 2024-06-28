import requests
import json
from pandas import DataFrame
from .model import TaxonReport
from .vocab import taxon_terms,required_taxonomy_columns
from .validate_required_fields import validate_required_fields

def create_taxonomy_report(dataframe: DataFrame,
                           num_matches: int = 5,
                           include_synonyms: bool = True,
                           ) -> TaxonReport:
    """
    Check if the given taxon in a data frame are valid for chosen atlas backbone.

    Parameters
    ----------
        dataframe : `pandas` dataframe
            the data frame to validate
        num_matches : int
            the maximum number of possible matches to return when searching for matches in chosen atlas
        include_synonyms : logical
            an option to include any synonyms of the identified taxon in your search

    Returns
    -------
        An object of class `TaxonReport` that givs information on invalid and unrecognised taxa, as well as
        suggested names for taxon that don't match the taxonomic backbone you are checking.
    """
    # check for scientificName, return None if it is not in the column names
    if "scientificName" not in list(dataframe.columns):
        return None
    
    # make a list of all scientific names in the dataframe
    scientific_names_list = list(set(dataframe["scientificName"]))

    # initialise has_invalid_taxa
    has_invalid_taxa=False
    
    # send list of scientific names to ALA to check their validity
    payload = [{"scientificName": name} for name in scientific_names_list]
    response = requests.request("POST","https://api.ala.org.au/namematching/api/searchAllByClassification",data=json.dumps(payload))
    response_json = response.json()
    terms = ["original name"] + ["proposed match(es)"] + ["rank of proposed match(es)"] + taxon_terms["Australia"]
    invalid_taxon_dict = {x: [] for x in terms}
    
    # loop over list of names and ensure we have gotten all the issues - might need to do single name search
    # to ensure we get everything
    for i,item in enumerate(scientific_names_list):
        item_index = next((index for (index, d) in enumerate(response_json) if "scientificName" in d and d["scientificName"] == item), None)
        # taxonomy["scientificName"][i] = item
        if item_index is None:
            # make this better
            has_invalid_taxa = True
            response_single = requests.get("https://api.ala.org.au/namematching/api/autocomplete?q={}&max={}&includeSynonyms={}".format("%20".join(item.split(" ")),num_matches,str(include_synonyms).lower()))
            response_json_single = response_single.json()
            if response_json_single:
                if response_json_single[0]['rank'] is not None:
                    invalid_taxon_dict["original name"].append(item)
                    invalid_taxon_dict["proposed match(es)"].append(response_json_single[0]['name'])
                    invalid_taxon_dict["rank of proposed match(es)"].append(response_json_single[0]['rank'])
                    for term in taxon_terms["Australia"]:
                        if term in response_json_single[0]['cl']:
                            invalid_taxon_dict[term].append(response_json_single[0]['cl'][term])
                        else:
                            invalid_taxon_dict[term].append(None)
                else:

                    # check for synonyms
                    for synonym in response_json_single[0]["synonymMatch"]:
                        if synonym['rank'] is not None:
                            invalid_taxon_dict["original name"].append(item)
                            invalid_taxon_dict["proposed match(es)"].append(synonym['name'])
                            invalid_taxon_dict["rank of proposed match(es)"].append(synonym['rank'])
                            for term in taxon_terms["Australia"]:
                                if term in synonym['cl']:
                                    invalid_taxon_dict[term].append(synonym['cl'][term])
                            else:
                                invalid_taxon_dict[term].append(None)
                        else:
                            print("synonym doesn't match")
            else:

                # try one last time to find a match
                response_search = requests.get("https://api.ala.org.au/namematching/api/search?q={}".format("%20".join(item.split(" "))))
                response_search_json = response_search.json()            
                if response_search_json['success']:
                    invalid_taxon_dict["original name"].append(item)
                    invalid_taxon_dict["proposed match(es)"].append(response_search_json['scientificName'])
                    invalid_taxon_dict["rank of proposed match(es)"].append(response_search_json['rank'])
                    for term in taxon_terms["Australia"]:
                        if term in response_search_json:
                            invalid_taxon_dict[term].append(response_search_json[term])
                        else:
                            invalid_taxon_dict[term].append(None)
                else:
                    print("last ditch search did not work")
                    print(response_search_json)
                    import sys
                    sys.exit()
    
    valid_taxon_count = 999
    if not has_invalid_taxa:
        # now 
        valid_data = validate_required_fields(dataframe,required_taxonomy_columns)
        for entry in valid_data.items():
            if entry[0] != "vernacularName":
                if entry[1] < dataframe.shape[0]:
                    if entry[1] < valid_taxon_count:
                        valid_taxon_count = entry[1]
        if dataframe.shape[0] < valid_taxon_count:
            valid_taxon_count = dataframe.shape[0]
    else:
        valid_taxon_count = 0

    # return report on taxon
    return {
        "has_invalid_taxa": has_invalid_taxa,
        "unrecognised_taxa": invalid_taxon_dict,
        "valid_taxon_count": valid_taxon_count
    }