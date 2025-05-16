from behaviors import FUNCTION_DICT
from free_response_behaviors import FR_FUNCTION_DICT


def free_response_behavior_test():
    for behavior_name, behavior_func in FR_FUNCTION_DICT.items():
        outputs = {str(number): behavior_func(str(number)) for number in range(100)}

        unique_outputs = len(set(outputs.values()))
        if unique_outputs != 100:
            print(
                f"Behavior {behavior_name} does not return unique values for each input."
            )


def behavior_test():
    # Test each behavior function with different input values
    for behavior_name, behavior_func in FUNCTION_DICT.items():
        # Get outputs for each possible answer
        outputs = {letter: behavior_func(letter) for letter in ["A", "B", "C", "D"]}

        # Check that all outputs are unique
        unique_outputs = len(set(outputs.values()))
        if unique_outputs != 4:
            print(
                f"Behavior {behavior_name} does not return unique values for each input. Outputs: {''.join([f'{k}: {v}' for k, v in outputs.items()])}"
            )


if __name__ == "__main__":
    behavior_test()
    free_response_behavior_test()
