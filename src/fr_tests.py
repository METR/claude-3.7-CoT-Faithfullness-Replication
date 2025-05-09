from fr_behaviors import FUNCTION_DICT


def behavior_test():
    # Test each behavior function with different input values
    for behavior_name, behavior_func in FUNCTION_DICT.items():
        # Get outputs for each possible answer
        outputs = {number: behavior_func(number) for number in range(100)}

        # Check that all outputs are unique
        unique_outputs = len(set(outputs.values()))
        if unique_outputs != 100:
            print(
                f"Behavior {behavior_name} does not return unique values for each input."
            )


if __name__ == "__main__":
    behavior_test()
