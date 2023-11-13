import os
import logging
import datetime
import json
import csv
from typing import Dict, List, Callable, Union
from graph_of_thoughts import controller, operations, prompter, parser

import utils


class CWPrompter(prompter.Prompter):
    """
    SortingPrompter provides the generation of prompts specific to the sorting
    example for the language models.

    Inherits from the Prompter class and implements its abstract methods.
    """

    cw_prompt = """<Instruction>Verify whether the text includes claims that are checkworthy—claims that are verifiable, not opinions, and pertain to sensitive topics.</Instruction>

<Examples>
Input: The sun is shining.
Output: No

Input: Bodybuilder Doug Brignole died from a COVID-19 vaccine.
Output: Yes

Input: Tetanus vaccines contain a secret infertility ingredient.
Output: Yes

Input: I think Elton John is a good singer.
Output: No

</Examples>

Input: {input}
Output: """

    def generate_prompt(
        self, num_branches: int, original: str, current: str, method: str, **kwargs
    ) -> str:
        """
        Generate a generate prompt for the language model.

        :param num_branches: The number of responses the prompt should ask the LM to generate.
        :type num_branches: int
        :param original: Input list of numbers.
        :type original: str
        :param current: Intermediate solution.
        :type current: str
        :param method: Method for which the generate prompt is generated.
        :type method: str
        :param kwargs: Additional keyword arguments.
        :return: The generate prompt.
        :rtype: str
        :raise AssertionError: If the requested number of branches is not one.
        """

        if current is None or current == "":
            input = original
        else:
            input = current
        if method.startswith("io"):
            return self.cw_prompt.format(input=input)

    def aggregation_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        pass

    def improve_prompt(self, **kwargs) -> str:
        pass

    def validation_prompt(self, **kwargs) -> str:
        pass

    def score_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        pass


class CWParser(parser.Parser):
    """
    SortingParser provides the parsing of language model reponses specific to
    the sorting example.

    Inherits from the Parser class and implements its abstract methods.
    """

    def __init__(self) -> None:
        """
        Inits the response cache.
        """
        self.cache = {}

    def parse_aggregation_answer(
        self, states: List[Dict], texts: List[str]
    ) -> Union[Dict, List[Dict]]:
        pass

    def parse_improve_answer(
        self, states: List[Dict], texts: List[str]
    ) -> Union[Dict, List[Dict]]:
        pass

    def parse_score_answer(
        self, states: List[Dict], texts: List[str]
    ) -> Union[Dict, List[Dict]]:
        pass

    def parse_validation_answer(
        self, states: List[Dict], texts: List[str]
    ) -> Union[Dict, List[Dict]]:
        pass

    def parse_generate_answer(self, state: Dict, texts: List[str]) -> List[Dict]:
        """
        Parse the response from the language model for a generate prompt.

        :param state: The thought state used to generate the prompt.
        :type state: Dict
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought states after parsing the respones from the language model.
        :rtype: List[Dict]
        """
        new_states = []
        for text in texts:
            answers = text.strip().split()
            if len(answers) == 0:
                logging.warning(
                    f"Could not parse step answer: {text}. Returning empty list."
                )
                answer = "[]"
            elif len(answers) > 1:
                logging.warning(
                    f"Multiword answers found for step answer: {text}. Using the first one."
                )
                answer = answers[0]
            else: 
                answer = answers[0]

            new_state = state.copy()
            new_state["current"] = answer
            new_state["phase"] = 2
            new_states.append(new_state)
        return new_states


def io() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the IO method.

    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()

    operations_graph.append_operation(operations.Generate(1, 1))
    # operations_graph.append_operation(operations.Score(1, False, utils.num_errors))
    operations_graph.append_operation(operations.GroundTruth(utils.test_CW))

    return operations_graph


# def read_data(file_path):
#     data = []
#     with open(file_path, "r") as f:
#         reader = csv.reader(f,delimiter=',', quotechar='"', skipinitialspace=True)
#         next(reader)
#         for row in reader:
#             data.append([int(row[0]), row[1], row[2], row[3]])
#     return data


def make_result_folder(lm_name, methods):
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "results")):
        os.makedirs(os.path.join(os.path.dirname(__file__), "results"))
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    extra_info = f"{lm_name}_{'-'.join([method.__name__ for method in methods])}"
    folder_name = f"results/{extra_info}_{timestamp}"
    os.makedirs(os.path.join(os.path.dirname(__file__), folder_name))
    return folder_name


def run(
    data_ids: List[int],
    methods: List[Callable[[], operations.GraphOfOperations]],
    budget: float,
    lm_name: str,
    dataset,
) -> float:
    # path = os.path.join(os.path.dirname(__file__), file_name)
    # selected_data = read_data(path)
    folder_name = make_result_folder(lm_name, methods)

    config = {
        "data": dataset.data,
        "methods": [method.__name__ for method in methods],
        "lm": lm_name,
        "budget": budget,
    }

    logging.basicConfig(
        filename=f"{folder_name}/log.log",
        filemode="w",
        format="%(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
    )

    for method in methods:
        os.makedirs(
            os.path.join(os.path.dirname(__file__), folder_name, method.__name__)
        )

    for data in dataset.data:
        for method in methods:
            logging.info(f"Running method {method.__name__}")
            lm = controller.AzureChatGPT(
                "../../graph_of_thoughts/controller/config.json",
                model_name=lm_name,
                cache=True,
            )
            operations_graph = method()
            executor = controller.Controller(
                lm,
                operations_graph,
                CWPrompter(),
                CWParser(),
                {
                    "original": data[1],
                    "current": "",
                    "phase": 0,
                    "method": method.__name__,
                },
            )
            try:
                executor.run()
            except Exception as e:
                logging.error(f"Exception: {e}")
            path = os.path.join(
                os.path.dirname(__file__),
                folder_name,
                method.__name__,
                f"{data[0]}.json",
            )
            executor.output_graph(path)
    return lm.cost

if __name__ == "__main__":
    MODELNAME = "azurechatgpt"
    FILE = "factcheck.csv"
    BUDGET = 30
    d = utils.dataset_reader(FILE)
    samples = []
    approaches = [io]
    spent = run(samples, approaches, BUDGET, MODELNAME, d)
    logging.info(f"Spent {spent} out of {BUDGET} budget.")

    
    # print(d.lookup("I'm hungry. I need to eat breakfast",'Checkworthy'))
