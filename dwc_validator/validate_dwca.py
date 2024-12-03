"""
This module contains functions for validating Darwin Core Archives.
"""
# pylint: disable=no-name-in-module
import logging
from typing import List
from pandas import DataFrame
from dwca.read import DwCAReader
from dwca.darwincore.utils import qualname as qn
from dwc_validator import validate
from dwc_validator.breakdown import generate_breakdowns
from dwc_validator.model import DwCAValidationReport, DFValidationReport


def validate_archive(
        dwca: DwCAReader,
        id_fields: List[str] = None) -> DwCAValidationReport:
    """
    Validate a Darwin Core Archive, returning a :class:`DwCAValidationReport` instance.

    :param dwca: A :class:`DwCAReader` instance.
    :param id_fields: a list of fields to use as the id field(s) for the core dataframe. Optional.
    The default is ["occurrenceID"]. For event archives this argument is ignored
    :raises InvalidArchive: If the archive is invalid.
    """
    # create the dataframe from the core file
    core_file_location = dwca.descriptor.core.file_location
    core_df = dwca.pd_read(core_file_location, parse_dates=False)
    logging.info("Core record count: %s", len(core_df))

    extension_validation_reports = []
    breakdowns = {}
    core_type = dwca.descriptor.core.type
    dataset_type = "unknown"
    if core_type:
        dataset_type = core_type[core_type.rfind("/") + 1:]

    if dwca.descriptor.core.type == qn('Occurrence'):

        logging.info("Occurrence core type")
        fields = dwca.descriptor.core.fields

        if not id_fields:
            id_fields = ['occurrenceID']

        # if the id field is "occurrenceID" or another id_field, then it'll be in the core dataframe as "id",
        # passing the id_term to the validation function will allow it to check
        # the id field is populated
        id_term = get_id_dwc_term(core_df, fields)

        df_validation_report = validate.validate_occurrence_dataframe(
            core_df, id_fields, id_term)

    elif dwca.descriptor.core.type == qn('Event'):
        logging.info("Event core type")
        df_validation_report = validate.validate_event_dataframe(core_df)

    else:
        logging.info("Invalid core type: %s", dwca.descriptor.core.type)
        df_validation_report = DFValidationReport(record_type=dwca.descriptor.core.type,
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
    breakdowns.update(generate_breakdowns(core_df))

    # occ_df = None
    if dwca.descriptor.core.type == qn('Event') and dwca.descriptor.extensions:

        for extension in dwca.descriptor.extensions:
            if extension.type == qn('Occurrence'):

                occ_df = dwca.pd_read(
                    extension.file_location, parse_dates=False)

                # generate report for extension
                extension_validation_reports.append(
                    validate.validate_occurrence_dataframe(occ_df, id_fields))

                # add breakdowns
                breakdowns.update(generate_breakdowns(occ_df))

    return DwCAValidationReport(
        len(df_validation_report.errors) == 0,
        core_type=core_type,
        dataset_type=dataset_type,
        core_validation_report=df_validation_report,
        extension_validation_reports=extension_validation_reports,
        breakdowns=breakdowns
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
