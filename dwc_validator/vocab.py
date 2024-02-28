"""
Vocabularies for Darwin Core terms.
"""

test_columns_for_spatial_vocab = [
    "decimalLatitude", 
    "decimalLongitude", 
    "geodeticDatum",
    "coordinateUncertaintyInMeters"
]

unique_id_vocab = [
    "occurrenceID",
    "catalogNumber", 
    "recordNumber"
]

required_taxonomy_columns = [
    "scientificName",
    "vernacularName",
    "genus",
    "family",
    "order",
    "class", #classs
    "phylum",
    "kingdom"
]

required_columns_spatial_vocab = [
    "decimalLatitude", 
    "decimalLongitude", 
    "geodeticDatum",
    "coordinateUncertaintyInMeters",
]

required_columns_other_occ = [
    "basisOfRecord",
    "scientificName",
    "eventDate"
]

### TODO: FIX THIS
required_columns_other_event = [
    "basisOfRecord",
    "scientificName",
    "eventDate",
    "eventID"
]

# Vocabulary for Darwin Core term "basisOfRecord"
basis_of_record_vocabulary = [
    'PreservedSpecimen',
    'FossilSpecimen',
    'LivingSpecimen',
    'HumanObservation',
    'MachineObservation',
    'Observation',
    'MaterialSample',
    'Occurrence'
] 

required_multimedia_columns_occ = [
    "occurrenceID",
    "identifier"
]

required_multimedia_columns_event = [
    "eventID",
    "occurrenceID",
    "identifier"
]

required_emof_columns_event = [
    "eventID",
    "occurrenceID",
    "measurementID",
    "measurementType",
    "measurementValue",
    "measurementUnit",
    "measurementAccuracy"
]

# Vocabulary for Darwin Core term "geodeticDatum" - todo replace with an
# authoritative source
geodetic_datum_vocabulary = {
    'WGS84',
    'NAD83',
    'ETRS89',
    'ITRF',
    'GDA94',
    'ED50',
    'NAD27',
    'EPSG:20248',
    'AGD66',
    'AGD84',
    'EPSG:20249',
    'EPSG:20250',
    'EPSG:20251',
    'EPSG:20252',
    'EPSG:20253',
    'EPSG:20254',
    'EPSG:20255',
    'EPSG:20256',
    'EPSG:20257',
    'EPSG:20258',
    'EPSG:20348',
    'EPSG:20349',
    'EPSG:20350',
    'EPSG:20351',
    'EPSG:20352',
    'EPSG:20353',
    'EPSG:20354',
    'EPSG:20355',
    'EPSG:20356',
    'EPSG:20357',
    'EPSG:20358',
    'EPSG:28348',
    'EPSG:28349',
    'EPSG:28350',
    'EPSG:28351',
    'EPSG:28352',
    'EPSG:28353',
    'EPSG:28354',
    'EPSG:28355',
    'EPSG:28356',
    'EPSG:28357',
    'EPSG:32601',
    'EPSG:32602',
    'EPSG:32603',
    'EPSG:32604',
    'EPSG:32605',
    'EPSG:32606',
    'EPSG:32607',
    'EPSG:32608',
    'EPSG:32609',
    'EPSG:32610',
    'EPSG:32611',
    'EPSG:32612',
    'EPSG:32613',
    'EPSG:32614',
    'EPSG:32615',
    'EPSG:32616',
    'EPSG:32617',
    'EPSG:32618',
    'EPSG:32619',
    'EPSG:32620',
    'EPSG:32621',
    'EPSG:32622',
    'EPSG:32623',
    'EPSG:32624',
    'EPSG:32625',
    'EPSG:32626',
    'EPSG:32627',
    'EPSG:32628',
    'EPSG:32629',
    'EPSG:32630',
    'EPSG:32631',
    'EPSG:32632',
    'EPSG:32633',
    'EPSG:32634',
    'EPSG:32635',
    'EPSG:32636',
    'EPSG:32637',
    'EPSG:32638',
    'EPSG:32639',
    'EPSG:32640',
    'EPSG:32641',
    'EPSG:32642',
    'EPSG:32643',
    'EPSG:32644',
    'EPSG:32645',
    'EPSG:32646',
    'EPSG:32647',
    'EPSG:32648',
    'EPSG:32649',
    'EPSG:32650',
    'EPSG:32651',
    'EPSG:32652',
    'EPSG:32653',
    'EPSG:32654',
    'EPSG:32655',
    'EPSG:32656',
    'EPSG:32657',
    'EPSG:32658',
    'EPSG:32659',
    'EPSG:32660',
    'EPSG:32701',
    'EPSG:32702',
    'EPSG:32703',
    'EPSG:32704',
    'EPSG:32705',
    'EPSG:32706',
    'EPSG:32707',
    'EPSG:32708',
    'EPSG:32709',
    'EPSG:32710',
    'EPSG:32711',
    'EPSG:32712',
    'EPSG:32713',
    'EPSG:32714',
    'EPSG:32715',
    'EPSG:32716',
    'EPSG:32717',
    'EPSG:32718',
    'EPSG:32719',
    'EPSG:32720',
    'EPSG:32721',
    'EPSG:32722',
    'EPSG:32723',
    'EPSG:32724',
    'EPSG:32725',
    'EPSG:32726',
    'EPSG:32727',
    'EPSG:32728',
    'EPSG:32729',
    'EPSG:32730',
    'EPSG:32731',
    'EPSG:32732',
    'EPSG:32733',
    'EPSG:32734',
    'EPSG:32735',
    'EPSG:32736',
    'EPSG:32737',
    'EPSG:32738',
    'EPSG:32739',
    'EPSG:32740',
    'EPSG:32741',
    'EPSG:32742',
    'EPSG:32743',
    'EPSG:32744',
    'EPSG:32745',
    'EPSG:32746',
    'EPSG:32747',
    'EPSG:32748',
    'EPSG:32749',
    'EPSG:32750',
    'EPSG:32751',
    'EPSG:32752',
    'EPSG:32753',
    'EPSG:32754',
    'EPSG:32755',
    'EPSG:32756',
    'EPSG:32757',
    'EPSG:32758',
    'EPSG:32759',
    'EPSG:32760'
}

taxon_terms = {
    "Australia": ["scientificName","rank","species","genus","family","order","classs","phylum","kingdom"],
    "ALA": ["scientificName","rank","species","genus","family","order","classs","phylum","kingdom"]
}

name_matching_terms = {
    "Australia": ["scientificName","scientificNameAuthorship","rank","species","genus","family","order","classs","phylum","kingdom"],
    "ALA": ["scientificName","scientificNameAuthorship","rank","species","genus","family","order","classs","phylum","kingdom"]
}
