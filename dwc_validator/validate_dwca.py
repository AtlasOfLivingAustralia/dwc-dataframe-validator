"""
This module contains functions for validating Darwin Core Archives.
"""
# pylint: disable=no-name-in-module
import logging
from typing import List
from pandas import DataFrame
from dwca.exceptions import InvalidSimpleArchive
from dwca.read import DwCAReader
from dwca.darwincore.utils import qualname as qn
from dwc_validator.breakdown import generate_breakdowns
from .validate_occurrence_dataframe import validate_occurrence_dataframe
from .validate_event_dataframe import validate_event_dataframe
from .validate_multimedia_extension import validate_media_extension
from .validate_emof_extension import validate_emof_extension
from dwc_validator.model import DwCAValidationReport, DFValidationReport
import zipfile
import json

def validate_archive(
        dwca_name: str = None,
        id_fields: List[str] = None,
        occurrences_check: bool = False,
        events_check: bool = False,
        multimedia_check: bool = False,
        emof_check: bool = False
        ) -> dict:
    """
    Validate a Darwin Core Archive, returning a :class:`DwCAValidationReport` instance.

    :param dwca: A :class:`DwCAReader` instance.
    :param id_fields: a list of fields to use as the id field(s) for the core dataframe. Optional.
    The default is ["occurrenceID"]. For event archives this argument is ignored
    :raises InvalidArchive: If the archive is invalid.
    """
    errors = []

    # try loading archive
    try:
        archive = DwCAReader(dwca_name)

    except InvalidSimpleArchive as e:
        
        # add to errors
        errors.append(str(e))

        # open archive as zipfile to check what files are in there
        archive_zip = zipfile.ZipFile(dwca_name)
        if len(archive_zip.filelist) < 3:
            errors.append("You are missing one or more of three files: occurrences.txt, eml.xml, or meta.xml")
        
        # return report
        return json.dumps({
            "valid": False,
            "core_type": None, 
            "dataset_type": None,
            "core_validation_report": None, 
            "extension_validation_reports": None,
            "breakdowns": None,
            "errors": errors
        })
        

    # second check
    if archive.descriptor is None:
        
        # open the archive as a zip file this time
        archive_zip = zipfile.ZipFile(dwca_name)

        # check to see if they have the minimum files
        if len(archive_zip.filelist) < 3:
            errors.append("You are missing one or more of three files: occurrences.txt, eml.xml, or meta.xml")
        
        # return the report
        return json.dumps({
            "valid": False,
            "core_type": None, 
            "dataset_type": None,
            "core_validation_report": None, 
            "extension_validation_reports": None,
            "breakdowns": None,
            "errors": errors
        })

    # create the dataframe from the core file
    try:
        core_df = archive.pd_read(archive.descriptor.core.file_location, parse_dates=False)
    except ValueError as e:
        return json.dumps({
            "valid": False,
            "core_type": None, 
            "dataset_type": None,
            "core_validation_report": None, 
            "extension_validation_reports": None,
            "breakdowns": None,
            "errors": [str(e)]
        })
    
    logging.info("Core record count: %s", len(core_df))

    errors = []
    extension_validation_reports = []
    # breakdowns = {}
    core_type = archive.descriptor.core.type
    dataset_type = "unknown"
    if core_type:
        dataset_type = core_type[core_type.rfind("/") + 1:]

    fields = archive.descriptor.core.fields
    id_term = get_id_dwc_term(core_df, fields)

    if archive.descriptor.core.type == qn('Occurrence'):
        
        if occurrences_check:

            logging.info("Occurrence core type")
            print("testing occurrences")
            fields = archive.descriptor.core.fields

            if not id_fields:
                id_fields = ['occurrenceID']

            occurrence_validation_report = validate_occurrence_dataframe(
                core_df, id_fields)

        else:

            occurrence_validation_report = None

        if archive.descriptor.extensions:
            print("Multimedia occurrences")
            print(archive.descriptor.extensions)
            if multimedia_check:
                print("need to figure out how to get multimedia extension working")
                import sys
                sys.exit()
                extension_validation_reports = validate_media_extension()
            else:
                extension_validation_reports = None

        # return the report
        return json.dumps({
            "valid": True,
            "core_type": None, 
            "dataset_type": None,
            "occurrence_validation_report": occurrence_validation_report, 
            "extension_validation_reports": None,
            "breakdowns": None,
            "errors": errors
        })

    elif archive.descriptor.core.type == qn('Event'):
        
        if events_check:
            print("need to double check this")
            print(core_df)
            import sys
            sys.exit()
            events_validation_report = validate_event_dataframe(core_df)
        else:
            events_validation_report = None

        logging.info("Event core type")
        # df_validation_report = validate_event_dataframe(core_df)

        if occurrences_check:

            logging.info("Occurrence core type")
            fields = archive.descriptor.core.fields

            if not id_fields:
                id_fields = ['occurrenceID']

            occurrence_validation_report = validate_occurrence_dataframe(
                core_df, id_fields)

        else:

            occurrence_validation_report = None

        if multimedia_check:
            n=1
        else:
            n=1

        if emof_check:
            n=1
        else:
            n=1

    else:
        logging.info("Invalid core type: %s", archive.descriptor.core.type)
        df_validation_report = DFValidationReport(record_type=archive.descriptor.core.type,
                                                  errors=["UNSUPPORTED_CORE_TYPE"],
                                                  warnings=[],
                                                  column_counts={},
                                                  record_count=0,
                                                  record_error_count=0,
                                                  coordinates_report=None,
                                                  records_with_taxonomy_count=0,
                                                  records_with_temporal_count=0,
                                                  records_with_recorded_by_count=0
      )

    # add breakdowns
    # breakdowns.update(generate_breakdowns(core_df))

    # # occ_df = None
    # if dwca.descriptor.core.type == qn('Event') and dwca.descriptor.extensions:

    #     for extension in dwca.descriptor.extensions:
    #         if extension.type == qn('Occurrence'):

    #             occ_df = dwca.pd_read(
    #                 extension.file_location, parse_dates=False)

    #             # generate report for extension
    #             extension_validation_reports.append(
    #                 validate.validate_occurrence_dataframe(occ_df, id_fields))

    #             # add breakdowns
    #             # breakdowns.update(generate_breakdowns(occ_df))

    # add occurrence_validation_report

    return DwCAValidationReport(
        len(errors) == 0,
        core_type=core_type,
        dataset_type=dataset_type,
        core_validation_report=df_validation_report,
        extension_validation_reports=extension_validation_reports,
        breakdowns=None
    )


def get_id_dwc_term(dataframe: DataFrame, fields):
    """
    Get the id term for the core dataframe
    :param dataframe:
    :param fields:
    :return:
    """
    id_term = None
    if "id" in dataframe.columns:
        col_idx = dataframe.columns.get_loc("id")
        matching_fields = [field["term"] for field in fields if field.get("index") == col_idx]

        if matching_fields:
            qualified_term = next(filter(None, matching_fields), None)

            if qualified_term:
                id_term = qualified_term.rsplit("/", 1)[-1]
    return id_term
