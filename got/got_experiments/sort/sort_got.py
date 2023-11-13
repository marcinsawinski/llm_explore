import os
import logging
import datetime
import json
import csv
from typing import Dict, List, Callable, Union
from graph_of_thoughts import controller, operations, prompter, parser
import utils


class SortingPrompter(prompter.Prompter):
    """
    SortingPrompter provides the generation of prompts specific to the sorting
    example for the language models.

    Inherits from the Prompter class and implements its abstract methods.
    """

    sort_prompt = """<Instruction> Sort the following list of numbers in ascending order. Output only the sorted list of numbers, no additional text. </Instruction>

<Examples>
Input: [5, 1, 0, 1, 2, 0, 4, 8, 1, 9, 5, 1, 3, 3, 9, 7]
Output: [0, 0, 1, 1, 1, 1, 2, 3, 3, 4, 5, 5, 7, 8, 9, 9]

Input: [3, 7, 0, 2, 8, 1, 2, 2, 2, 4, 7, 8, 5, 5, 3, 9, 4, 3, 5, 6, 6, 4, 4, 5, 2, 0, 9, 3, 3, 9, 2, 1]
Output: [0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 9]

Input: [4, 4, 9, 7, 9, 7, 0, 0, 4, 9, 1, 7, 9, 5, 8, 7, 5, 6, 3, 8, 6, 7, 5, 8, 5, 0, 6, 3, 7, 0, 5, 3, 7, 5, 2, 4, 4, 9, 0, 7, 8, 2, 7, 7, 7, 2, 1, 3, 9, 9, 7, 9, 6, 6, 4, 5, 4, 2, 0, 8, 9, 0, 2, 2]
Output: [0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9, 9]
</Examples>

Input: {input}"""

    got_split_prompt = """<Instruction> Split the following list of 8 numbers into 2 lists of 4 numbers each, the first list should contain the first 4 numbers and the second list the second 4 numbers.
Only output the final 2 lists in the following format without any additional text or thoughts!:
{{
    "List 1": [3, 4, 3, 5],
    "List 2": [2, 9, 2, 4]
}} </Instruction>

<Example>
Input: [9, 6, 7, 7, 2, 0, 2, 2]
Output: 
{{
    "List 1": [9, 6, 7, 7],
    "List 2": [2, 0, 2, 2]
}}
</Example>

Input: {input}"""
    got_merge_prompt = """<Instruction> Merge the following 2 sorted lists of length {length1} each, into one sorted list of length {length2} using a merge sort style approach.
Only output the final merged list without any additional text or thoughts!:</Instruction>

<Approach>
To merge the two lists in a merge-sort style approach, foloow these steps:
1. Compare the first element of both lists.
2. Append the smaller element to the merged list and move to the next element in the list from which the smaller element came.
3. Repeat steps 1 and 2 until one of the lists is empty.
4. Append the remaining elements of the non-empty list to the merged list.
</Approach>

Merge the following two lists into one sorted list:
1: {input1}
2: {input2}

Merged list:
"""
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

        if method.startswith("got"):
            if current is None or current == "":
                return self.got_split_prompt.format(input=input)
            # if current is just a sublist of the original input, return the split prompt
            if kwargs["phase"] == 1:
                return self.sort_prompt.format(input=current)

            if (
                "unsorted_sublist" in kwargs
                and kwargs["unsorted_sublist"] != ""
                and len(kwargs["unsorted_sublist"]) < len(original) - 5
            ):
                original = kwargs["unsorted_sublist"]

            return self.tot_improve_prompt.format(
                input=original,
                incorrectly_sorted=current,
                length=len(utils.string_to_list(original)),
            )

    def aggregation_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        """
        Generate an aggregation prompt for the language model.

        :param state_dicts: The thought states that should be aggregated.
        :type state_dicts: List[Dict]
        :param kwargs: Additional keyword arguments.
        :return: The aggregation prompt.
        :rtype: str
        :raise AssertionError: If not exactly two thought states are provided.
        """
        assert len(state_dicts) == 2, "Expected two states for aggregation prompt."
        len_input1 = len(utils.string_to_list(state_dicts[0]["current"]))
        len_input2 = len(utils.string_to_list(state_dicts[1]["current"]))
        if len_input1 == len_input2:
            length = len_input1
        elif len_input1 + len_input2 - 32 <= 16:
            length = 16
        else:
            length = 32

        return self.got_merge_prompt.format(
            input1=state_dicts[0]["current"],
            input2=state_dicts[1]["current"],
            length1=length,
            length2=length * 2,
        )

    def improve_prompt(self, **kwargs) -> str:
        pass

    def validation_prompt(self, **kwargs) -> str:
        pass

    def score_prompt(self, state_dicts: List[Dict], **kwargs) -> str:
        pass


class SortingParser(parser.Parser):
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
        """
        Parse the response from the language model for an aggregation prompt.

        :param states: The thought states used to generate the prompt.
        :type states: List[Dict]
        :param texts: The responses to the prompt from the language model.
        :type texts: List[str]
        :return: The new thought states after parsing the respones from the language model.
        :rtype: Union[Dict, List[Dict]]
        :raise AssertionError: If not exactly two thought states are provided.
        """

        assert len(states) == 2, "Expected two states for aggregation answer."
        new_states = []
        for text in texts:
            answers = text.strip().split("\n")
            if any(["Output" in answer for answer in answers]):
                # cut elements until last output is found
                for answer in reversed(answers):
                    if "Output" in answer:
                        answers = answers[answers.index(answer) :]
                        break

            answers_stripped = [
                answer for answer in answers if "[" in answer and "]" in answer
            ]
            if len(answers_stripped) == 0:
                for answer in answers:
                    answer = "[" + answer + "]"
                    try:
                        answer_converted = utils.string_to_list(answer)
                        if len(answer_converted) > 0:
                            answers_stripped.append(answer)
                    except:
                        pass
            if len(answers_stripped) == 0:
                logging.warning(
                    f"Could not parse aggregation answer: {text}. Returning empty list."
                )
                answer = "[]"
            else:
                answer = [
                    answer[answer.index("[") : answer.index("]") + 1]
                    for answer in answers_stripped
                ][0]
            states = sorted(states, key=lambda x: x["part"])
            merged_unsorted_sublists = (
                states[0]["unsorted_sublist"][:-1]
                + ", "
                + states[1]["unsorted_sublist"][1:]
            )
            new_state = states[0].copy()
            new_state["current"] = answer
            new_state["unsorted_sublist"] = merged_unsorted_sublists
            new_states.append(new_state)
        return new_states

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
            if state["method"] == "got" and state["current"] == "":
                # We expect a json which contains the four lists named "List 1" to "List 4"
                # cut everything until the opening bracket and everything after the closing bracket
                try:
                    text = text[text.index("{") : text.index("}") + 1]
                    json_dict = json.loads(text)
                    if len(json_dict.keys()) != 2:
                        logging.warning(
                            f"Expected 2 lists in json, but found {len(json_dict.keys())}."
                        )
                    for key, value in json_dict.items():
                        if "List" not in key:
                            logging.warning(
                                f"Expected key to contain 'List', but found {key}."
                            )
                            continue
                        if not isinstance(value, list):
                            value = utils.string_to_list(value)
                        new_state = state.copy()
                        new_state["current"] = str(value)
                        new_state["unsorted_sublist"] = str(value)
                        new_state["phase"] = 1
                        new_state["part"] = key
                        new_states.append(new_state)
                except Exception as e:
                    logging.error(
                        f"Could not parse step answer: {text}. Encountered exception: {e}"
                    )
            else:
                answers = text.strip().split("\n")
                answers = [
                    answer for answer in answers if "[" in answer and "]" in answer
                ]
                if any(["Output" in answer for answer in answers]):
                    # cut elements until last output is found
                    for answer in reversed(answers):
                        if "Output" in answer:
                            answers = answers[answers.index(answer) :]
                            break

                answers = [
                    answer[answer.index("[") : answer.index("]") + 1]
                    for answer in answers
                ]
                if len(answers) == 0:
                    logging.warning(
                        f"Could not parse step answer: {text}. Returning empty list."
                    )
                    answer = "[]"
                else:
                    if len(answers) > 1:
                        logging.warning(
                            f"Multiple answers found for step answer: {text}. Using the first one."
                        )
                    answer = answers[0]

                new_state = state.copy()
                new_state["current"] = answer
                new_state["phase"] = 2
                new_states.append(new_state)
        return new_states

def got() -> operations.GraphOfOperations:
    """
    Generates the Graph of Operations for the GoT method.

    :return: Graph of Operations
    :rtype: GraphOfOperations
    """
    operations_graph = operations.GraphOfOperations()

    plans = operations.Generate(2, 1)
    operations_graph.append_operation(plans)  # generate the sublists
    for i in range(1, 3):
        list_id = f"List {i}"
        sub_list = operations.Selector(
            lambda thoughts, list_id=list_id: [
                thought for thought in thoughts if thought.state["part"] == list_id
            ]
        )
        sub_list.add_predecessor(plans)
        operations_graph.add_operation(sub_list)
        sort_sub_list = operations.Generate(1, 5)
        sort_sub_list.add_predecessor(sub_list)
        operations_graph.add_operation(sort_sub_list)
        score_sub_list = operations.Score(1, False, utils.num_errors)
        score_sub_list.add_predecessor(sort_sub_list)
        operations_graph.add_operation(score_sub_list)
        keep_best_sub_list = operations.KeepBestN(1, False)
        keep_best_sub_list.add_predecessor(score_sub_list)
        operations_graph.add_operation(keep_best_sub_list)

    final_aggregate = operations.Aggregate(10)
    operations_graph.append_operation(final_aggregate)
    operations_graph.append_operation(operations.Score(1, False, utils.num_errors))
    keep_best_aggregate_final = operations.KeepBestN(1, False)
    operations_graph.append_operation(keep_best_aggregate_final)

    operations_graph.append_operation(operations.Generate(1, 10))
    score_aggr_3 = operations.Score(1, False, utils.num_errors)
    score_aggr_3.add_predecessor(keep_best_aggregate_final)
    operations_graph.append_operation(score_aggr_3)
    operations_graph.append_operation(operations.KeepBestN(1, False))

    operations_graph.append_operation(operations.GroundTruth(utils.test_sorting))

    return operations_graph

def read_data(file_path):
    data = []
    with open(file_path, "r") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            data.append([int(row[0]), row[1], row[2]])
    return data
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
) -> float:
    path = os.path.join(os.path.dirname(__file__), "sort.csv")
    selected_data = read_data(path)
    folder_name = make_result_folder(lm_name,methods)
    
    config = {
    "data": selected_data,
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

    for data in selected_data:
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
                SortingPrompter(),
                SortingParser(),
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
    budget = 30
    samples = []
    approaches = [got]
    spent = run(samples, approaches, budget, "azurechatgpt")
    logging.info(f"Spent {spent} out of {budget} budget.")