# Darwin core data frame validator

[![Pylint](https://github.com/djtfmartin/dwc-dataframe-validator/actions/workflows/pylint.yml/badge.svg)](https://github.com/djtfmartin/dwc-dataframe-validator/actions/workflows/pylint.yml)
[![Python package](https://github.com/djtfmartin/dwc-dataframe-validator/actions/workflows/python-package.yml/badge.svg)](https://github.com/djtfmartin/dwc-dataframe-validator/actions/workflows/python-package.yml)

This is a basic validator for DwC python data frames and DwC archives. 
It only validates the DwC data frames for `Occurrence` and `Event` datasets.
This intended to give basic validation on datasets before they are published to an aggregator such as the ALA.

This includes:
* Checking unique identifier fields (e.g. `occurrenceID`, `eventID`) are populated for all rows and are unique 
* Basic checking of coordinate fields (`decimalLatitude`, `decimalLongitude`)
* Checking numeric fields are populated with numeric values
* Checking fields that should be using a controlled vocabulary are populated with values from the vocabulary (e.g. basisOfRecord)

# Errors and warnings

The validator will return a list of errors and warnings. 
Errors are issues that will prevent the dataset from being published.
Warnings are issues that should be fixed before the dataset is published.

## Errors

Current errors are:
* Missing unique identifier fields
* Duplicate unique identifier values

## Warnings

Current warnings are:
* Invalid coordinate values - non-numeric values or values outside of the valid range
* Invalid numeric values in numeric fields e.g. `coordinatePrecision`, depth
* Invalid values for fields that should be using a controlled vocabulary e.g. `basisOfRecord`

## Dependencies

This library is reliant on the [python-dwca-reader](https://github.com/BelgianBiodiversityPlatform/python-dwca-reader) library for reading and parsing DwC archives.

## Example usage

```python
import jsonpickle
import pandas as pd
from dwc_validator.validate import validate_occurrence_dataframe

# create example dataframe
rows = [
    {"scientificName": "SpeciesA", "decimalLatitude": 40.7128, "decimalLongitude": -74.0060, "eventDate": "2023-01-01", "recordedBy": "John Doe"},
    {"scientificName": "SpeciesB", "decimalLatitude": 34.0522, "decimalLongitude": -118.2437, "eventDate": "2023-02-15", "recordedBy": "Jane Smith"},
    {"scientificName": "SpeciesC", "decimalLatitude": 51.5074, "decimalLongitude": -0.1278, "eventDate": "2023-03-30", "recordedBy": "Bob Johnson"}
]
dwc_df = pd.DataFrame(rows)

# Validate a data frame
validation_report = validate_occurrence_dataframe(dwc_df)

# View report in JSON
print(jsonpickle.encode(validation_report, unpicklable=False, indent=2))
```

Will output
```json
{
  "record_count": 3,
  "errors": [],
  "warnings": [],
  "coordinates_report": {
    "has_coordinates_fields": true,
    "invalid_decimal_latitude_count": 0,
    "invalid_decimal_longitude_count": 0
  },
  "column_counts": {
    "scientificName": 3,
    "decimalLatitude": 3,
    "decimalLongitude": 3,
    "eventDate": 3,
    "recordedBy": 3
  },
  "record_error_count": 0,
  "records_with_taxonomy_count": 3,
  "records_with_temporal_count": 3,
  "records_with_recorded_by_count": 3,
  "vocab_reports": [
    {
      "field": "basisOfRecord",
      "has_field": false,
      "recognised_count": 0,
      "unrecognised_count": 0,
      "non_matching_values": []
    },
    {
      "field": "geodeticDatum",
      "has_field": false,
      "recognised_count": 0,
      "unrecognised_count": 0,
      "non_matching_values": []
    }
  ]
}

```


## Local dev setup

```bash

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

To validate a full archive, see the [example](DwCA.md).

## Running tests

```bash
pip install -r requirements.txt
pip install pytest pytest-coverage
pytest --cov
pylint --max-line-length=120 $(git ls-files '*.py')
```


