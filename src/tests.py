from free_response_behaviors import FR_FUNCTION_DICT


def free_response_behavior_test():
    for behavior_name, behavior_func in FR_FUNCTION_DICT.items():
        outputs = {str(number): behavior_func(str(number)) for number in range(100)}

        unique_outputs = len(set(outputs.values()))
        if unique_outputs != 100:
            print(
                f"Behavior {behavior_name} does not return unique values for each input."
            )


if __name__ == "__main__":
    free_response_behavior_test()
