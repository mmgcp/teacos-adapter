import sys
from copy import copy
from dataclasses import dataclass
from typing import Optional

from loguru import logger

import re
from test_api import run_adapter as run_teacos_adapter
from abm_model_april import run_model as run_abm_model
from tno.aimms_adapter.data_types import TeacosAdapterConfig
from datetime import datetime
from pathlib import Path


def get_a_t_from_path(path: Path):
    # Get a, t from config.output_esdl_file_path using regex
    a, t = re.findall(r"_A=(\d+)_T=(\d+)", str(output_esdl_file_path))[0]
    a, t = int(a), int(t)
    return a, t


def main(config: 'TeacosAdapterConfig') -> dict:
    """TEACOS run"""
    logger.info(f"Full run with {config=}")
    logger.info("Running TEACOS adapter...")
    run_teacos_adapter(config)  # Saves model under config.output_esdl_file_path
    logger.info("Run completed.")

    '''ABM run'''
    logger.info("Running ABM Model - April...")

    abm_kwargs = dict(
        radius=0.0075,
        budget=1000,
        TEACOS_input=50000,
        PVPanelBatchSize=2,
        CostOfPVPanel=500,
        steps=12,
    )

    a, t = get_a_t_from_path(config.output_esdl_file_path)
    abm_output_esdl_file_path = save_file_path(config.output_esdl_file_path, a + 1, t)

    # Use the output from TEACOS as input for the ABM run
    outcomes = run_abm_model(
        config=TeacosAdapterConfig(
            input_esdl_file_path=str(config.output_esdl_file_path),
            output_esdl_file_path=str(abm_output_esdl_file_path),
        ),
        **abm_kwargs
    )
    logger.info(f"Run completed. Outcomes: {outcomes}")
    return outcomes


OUTPUT_FOLDER = Path("output")
"""
if __name__ == "__main__":
    # TODO:
    #   - Create plots

    folder_name = datetime.today().isoformat()

    input_esdl_file_path = Path("ESDLs-Input/28_Pand van Dave Verkeersopleidingen_Solo.esdl")
    output_esdl_file_path = (
            OUTPUT_FOLDER / folder_name / input_esdl_file_path.stem
    )
    output_esdl_file_path = save_file_path(output_esdl_file_path, 0, 1)
    output_esdl_file_path.parent.mkdir(parents=True, exist_ok=True)

    ''' Configures the data input for the whole thing '''
    config = TeacosAdapterConfig(
        input_esdl_file_path=str(input_esdl_file_path),
        output_esdl_file_path=str(output_esdl_file_path),
    )

    for i in range(1):
        logger.info(f"Starting iteration {i}")
        outcomes = main(config)
        '''Adjust the configuration for TEACOS as the loop progresses'''

        input_esdl_file_path = config.output_esdl_file_path
        a, t = get_a_t_from_path(input_esdl_file_path)
        input_esdl_file_path = save_file_path(input_esdl_file_path, a + 1, t)
        output_esdl_file_path = save_file_path(input_esdl_file_path, a + 1, t + 1)

        config = TeacosAdapterConfig(
            input_esdl_file_path=str(input_esdl_file_path),
            output_esdl_file_path=str(output_esdl_file_path),
        )

    # Load ESDL with config.output_esdl_file_path
    # Create Sankey diagram for energy flows
    # Write diagram to folder

    logger.success("Run complete.")
"""
