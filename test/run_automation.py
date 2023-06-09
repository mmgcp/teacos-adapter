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
from sankeyDiagram import generate_sankey
import json


logger.remove()
logger.add(sys.stderr, level="DEBUG")  # Logging verbosity. Can be "WARNING", "INFO", "DEBUG", "TRACE"


def save_file_path(path: Path | str, a: int, t: int) -> Path:
    """Format file path so that its name ends with '_A={a}_T={t}.<suffix>'.

    If such a pattern already exists, remove entirely using regex and replace with new values.
    """
    if isinstance(path, str):
        path = Path(path)

    path = Path(re.sub(r"_A=\d+_T=\d+", "", str(path)))
    return path.with_name(path.stem + f"_A={a}_T={t}" + path.suffix)

'''Set the outputh path and the number of iterations'''
OUTPUT_FOLDER = Path("output")
N_ITERATIONS = 13


def automation_done_right():
    a = 0
    t = 1
    TEACOSresults = {}
    ABMresults = {}

    ''' Decide the initial input file to run and the output folder name '''
    input_esdl_file_path = Path("ESDLs-Input/Tholen.esdl")
    folder_name = str(input_esdl_file_path.stem) + "_Iterations_" + str(N_ITERATIONS) + "_Time_" + datetime.today().isoformat()
    base_filename = input_esdl_file_path.stem
    base_output_esdl_file_path = (
            OUTPUT_FOLDER / folder_name / base_filename
    )
    output_esdl_file_path = save_file_path(base_output_esdl_file_path, a, t)
    output_esdl_file_path.parent.mkdir(parents=True, exist_ok=True)

    ''' Set the config for the first run'''
    config = TeacosAdapterConfig(
        input_esdl_file_path=str(input_esdl_file_path),
        output_esdl_file_path=str(output_esdl_file_path),
    )

    ''' Determine the setup for the iterations'''
    for i in range(N_ITERATIONS):

        ''' These variables are used to save results of the iterations'''
        TEACOSDecision = None
        TEACOSPower = None
        logger.info(f"Full run with {config=}")
        logger.info("Running TEACOS adapter...")
        run_teacos_adapter(config)  # Saves model under config.output_esdl_file_path
        logger.info("Run completed.")

        ''' Sankey Diagram of TEACOS output '''
        logger.info("Generating Sankey Diagram...")
        TEACOSDecision, TEACOSPower, AgentsMJ = generate_sankey(config.output_esdl_file_path, TEACOSDecision, TEACOSPower)
        logger.info("Sankey Diagram for TEACOS generated.")
        TEACOSresults[i] = TEACOSPower
        '''ABM run'''
        abm_kwargs = dict(
            radius=0.0075,
            budget=1000000000,  # TODO: reset to 1000
            PVPanelBatchSize= 4, # TODO: reset to 2
            CostOfPVPanel=50, # TODO: reset to 500
            steps=12,
        )

        a += 1
        config = TeacosAdapterConfig(
            input_esdl_file_path=str(config.output_esdl_file_path),
            output_esdl_file_path=str(save_file_path(base_output_esdl_file_path, a, t))
        )

        logger.info("Running ABM Model - April... with config:" + str(config.input_esdl_file_path))
        # Use the output from TEACOS as input for the ABM run
        outcomes = run_abm_model(
            config=config,
            **abm_kwargs
        )
        logger.info(f"Run completed. Outcomes: {outcomes}")

        ''' Sankey Diagram '''
        logger.info("Generating Sankey Diagram...")
        TEACOSDecision, TEACOSPower, AgentsMJ = generate_sankey(config.output_esdl_file_path, TEACOSDecision, TEACOSPower)
        logger.info("Sankey Diagram for ABM generated.")
        ABMresults[i] = AgentsMJ
        logger.info(f"Progress of results: {ABMresults}, {TEACOSresults}")

        config = TeacosAdapterConfig(
            input_esdl_file_path=str(save_file_path(base_output_esdl_file_path, a, t)),
            output_esdl_file_path=str(save_file_path(base_output_esdl_file_path, a, t + 1))
        )
        t += 1

    ds = [TEACOSresults, ABMresults]
    resultsdict = {}
    for k in TEACOSresults.keys():
        resultsdict[k] = tuple(d[k] for d in ds)


    logger.info(f"{N_ITERATIONS} complete")
    logger.info(f"Results: {resultsdict}")
    jsonpath = base_output_esdl_file_path.parent / "results.json"
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    jsonpath.write_text(json.dumps(resultsdict, indent=4))
    logger.info(f"Results saved to results.json")


if __name__ == "__main__":
    automation_done_right()
