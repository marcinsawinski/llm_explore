# Copyright (c) 2023 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# main author: Nils Blach

from typing import Dict, List
import os
import csv
class dataset_reader():
    def __init__(self, file_name):
        self.file_name = file_name
        self.file_path = os.path.join(os.path.dirname(__file__), file_name)
        self.read_data()
    def lookup(self, claim:str, label_name:str) -> str:
        return(self.data_dict[claim][label_name])
    def read_data(self):
        self.data = []
        self.data_dict = dict()
        with open(self.file_path, "r") as f:
            reader = csv.reader(f,delimiter=',', quotechar='"', skipinitialspace=True)
            self.header = next(reader)
            for row in reader:
                self.data.append(row)
                self.data_dict.update({row[1]:{ self.header[2+i]:row[2+i] for i  in range(len(self.header[2:]))}})


FILE = "factcheck.csv"
d = dataset_reader(FILE)

def string_to_list(string: str) -> List[int]:
    """
    Helper function to convert a list encoded inside a string into a Python
    list object of string elements.

    :param string: Input string containing a list.
    :type string: str
    :return: List of string elements.
    :rtype: List[str]
    :raise AssertionError: If input string does not contain a list.
    """

    assert string[0] == "[" and string[-1] == "]", "String is not a list."
    return [int(num) for num in string[1:-1].split(",")]
def test_CW(state: Dict) -> bool:
    """
    Function to test whether the final solution matches ground truth.

    :param state: Thought state that represents the final solution.
    :type state: Dict
    :return: Returns whether the solution matches the ground truth.
    :rtype: bool
    """
    try:
        return d.lookup(state["original"],'Checkworthy') == state["current"]
    except:
        return False


def test_sorting(state: Dict) -> bool:
    """
    Function to test whether the final solution matches ground truth.

    :param state: Thought state that represents the final solution.
    :type state: Dict
    :return: Returns whether the solution matches the ground truth.
    :rtype: bool
    """

    try:
        correct_list = sorted(string_to_list(state["original"]))
        sorted_list = string_to_list(state["current"])
        return sorted_list == correct_list
    except:
        return False


def num_errors(state: Dict) -> float:
    """
    Function to locally count the number of errors that serves as a score.

    :param state: Thought state to be scored.
    :type state: Dict
    :return: Number of errors.
    :rtype: float
    """

    try:
        unsorted_list = state["original"]
        if (
            "unsorted_sublist" in state
            and state["unsorted_sublist"] != ""
            and state["unsorted_sublist"] is not None
            and len(state["unsorted_sublist"]) < len(unsorted_list) - 5
        ):
            unsorted_list = state["unsorted_sublist"]
        correct_list = sorted(string_to_list(unsorted_list))
        current_list = string_to_list(state["current"])
        num_errors = 0
        for i in range(10):
            num_errors += abs(
                sum([1 for num in current_list if num == i])
                - sum([1 for num in correct_list if num == i])
            )
        num_errors += sum(
            [1 for num1, num2 in zip(current_list, current_list[1:]) if num1 > num2]
        )
        return num_errors
    except:
        return 300
