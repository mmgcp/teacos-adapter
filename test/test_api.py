from dataclasses import asdict, dataclass
from time import sleep
from typing import Optional

import requests
from loguru import logger

from tno.aimms_adapter.data_types import TeacosAdapterConfig



def run_adapter(
    config: "TeacosAdapterConfig" = TeacosAdapterConfig(),
    api_endpoint: str = "http://localhost:9300",
):
    res = requests.get(api_endpoint + "/status")
    if res.ok:
        logger.info("Endpoint /status ok! ")
    else:
        logger.error("Endpoint /status not ok! ")
        exit(1)

    model_run_id = None
    res = requests.get(api_endpoint + "/model/request")
    if res.ok:
        logger.info("Endpoint /model/request ok!")
        result = res.json()
        logger.debug(f"Response: {result}")
        model_run_id = result["model_run_id"]
    else:
        logger.error("Endpoint /model/request not ok!")
        exit(1)

    post_body = asdict(config)

    res = requests.post(
        api_endpoint + "/model/initialize/" + model_run_id, json=post_body
    )
    if res.ok:
        logger.info("Endpoint /model/initialize ok!")
        result = res.json()
        logger.debug(f"Response: {result}")
    else:
        logger.error("Endpoint /model/initialize not ok!")
        exit(1)

    res = requests.get(api_endpoint + "/model/run/" + model_run_id)
    if res.ok:
        logger.info("Endpoint /model/run ok!")
        result = res.json()
        logger.debug(f"Response: {result}")
    else:
        logger.error("Endpoint /model/run not ok!")
        exit(1)

    succeeded = False
    while not succeeded:
        res = requests.get(api_endpoint + "/model/status/" + model_run_id)
        if res.ok:
            logger.info("Endpoint /model/status ok!")
            result = res.json()
            logger.debug(f"Response: {result}")
            if result["state"] == "SUCCEEDED":
                succeeded = True
            elif result["state"] == "ERROR":
                logger.debug(result["reason"])
                break
            else:
                sleep(2)
        else:
            logger.error("Endpoint /model/status not ok!")
            result = res.json()
            logger.debug(f"Response: {result}")
            exit(1)

    # res = requests.get(api_endpoint + '/model/results/' + model_run_id)
    # if res.ok:
    #     print("Endpoint /model/results ok!")
    #     result = res.json()
    #     print(result)
    # else:
    #     print("Endpoint /model/results not ok!")
    #     exit(1)

    res = requests.get(api_endpoint + "/model/remove/" + model_run_id)
    if res.ok:
        logger.info("Endpoint /model/remove ok!")
        result = res.json()
        logger.debug(result)
    else:
        logger.error("Endpoint /model/remove not ok!")
        exit(1)


if __name__ == "__main__":
    config = TeacosAdapterConfig(
        input_esdl_file_path="Only_TEACOS/Tholen_Manual_Input_2_Fixed.esdl",
        output_esdl_file_path="Only_TEACOS/Tholen_Manual_Output_2_Fixed.esdl"
    )
    run_adapter(config=config)
