import os
import logging
import datetime
import json
import csv
from typing import Dict, List, Callable, Union
from graph_of_thoughts import controller, operations, prompter, parser
# import utils

# print('path: ',os.getcwd())
# print(os.listdir())
# lm = controller.AzureChatGPT(
#                 "../graph_of_thoughts/controller/config.json",
#                 model_name='azurechatgpt',
#                 cache=True,
#             )
# print(lm)

def io() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the IO method.

    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()

    operations_graph.append_operation(operations.Generate(1, 1))
    operations_graph.append_operation(operations.Score(1, False, utils.num_errors))
    operations_graph.append_operation(operations.GroundTruth(utils.test_sorting))

    return operations_graph

def run(
    data_ids: List[int],
    methods: List[Callable[[], operations.GraphOfOperations]],
    budget: float,
    lm_name: str,
) -> float:
    pass
    return 0

if __name__ == "__main__":
    budget = 30
    samples = [item for item in range(0, 1)]
    approaches = [io]
    spent = run(samples, approaches, budget, "azurechatgpt")
    logging.info(f"Spent {spent} out of {budget} budget.")