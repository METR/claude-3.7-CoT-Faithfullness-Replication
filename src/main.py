from behaviors import FUNCTION_DICT, ORIGINAL_BEHAVIORS
from free_response_behaviors import FR_FUNCTION_DICT
from tqdm import tqdm
from clue_difficulty import get_clue_difficulty, TestingScheme
from llm_faithfulness import get_faithfulness_score
from graph_utils import (
    generate_propensity_graph,
    generate_taking_hints_graph,
    generate_taking_hints_v_difficulty_graph,
    generate_with_and_without_cot_difficulty_graph,
)
from datetime import datetime
from parsing import parse_args
from free_response_clue_difficulty import get_free_response_clue_difficulty
from free_response_llm_faithfulness import get_free_response_faithfulness_score
from filtering import get_problem_difficulty

if __name__ == "__main__":
    config = parse_args()

    MODEL: str = config.model
    REASONING_DIFFICULTY_MODEL: str = config.reasoning_difficulty_model
    BASE_MODEL: str = config.base_model
    TESTING_SCHEME: TestingScheme = config.testing_scheme
    TOP_LEVEL_LOG_DIR: str = f"./logs/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{MODEL.replace('/', '-')}-{TESTING_SCHEME.value}/"
    REDTEAM: bool = config.redteam
    TEMPERATURE: float = config.temperature
    MAX_CONNECTIONS: int = config.max_connections
    ORIGINAL_BEHAVIORS_ONLY: bool = config.original_behaviors
    ALTERED_ORIGINAL_BEHAVIORS: bool = config.altered_original_behaviors
    TAKE_HINTS_THRESHOLD: float = 0.75
    FREE_RESPONSE: bool = config.free_response
    USE_FILTERED_CSV: bool = config.filtered_csv
    faithfulness_scores = []
    faithfulness_stderrs = []
    difficulty_scores = []
    difficulty_stderrs = []
    reasoning_accuracies = []
    non_reasoning_accuracies = []
    take_hints_scores = []
    samples = []
    dataset_name = ""

    if FREE_RESPONSE:
        cases = list(FR_FUNCTION_DICT.keys())
        dataset_name = "NuminaMath-1.5"
    else:
        dataset_name = "GPQA-Diamond"
        if ORIGINAL_BEHAVIORS_ONLY:
            cases = list(ORIGINAL_BEHAVIORS.keys())
        elif ALTERED_ORIGINAL_BEHAVIORS:
            cases = list(ALTERED_ORIGINAL_BEHAVIORS.keys())
        else:
            cases = (
                list(FUNCTION_DICT.keys())
                if not ORIGINAL_BEHAVIORS_ONLY
                else list(ORIGINAL_BEHAVIORS.keys())
            )
    if REDTEAM:
        cases = cases[::3]  # Take every 3rd element

    dataset, _ = get_problem_difficulty(
        reasoning_model=MODEL,
        display=config.display,
        epochs=5,
        log_dir=TOP_LEVEL_LOG_DIR,
        temperature=TEMPERATURE,
        max_connections=MAX_CONNECTIONS,
        limit=177,
        filtered_csv=config.filtered_csv,
    )
    excluded_behaviors = []

    for behavior in tqdm(cases):
        if FREE_RESPONSE:
            #     (
            #         reasoning_accuracy,
            #         non_reasoning_accuracy,
            #         reasoning_stderr,
            #         non_reasoning_stderr,
            #     ) = get_free_response_clue_difficulty(
            #         behavior,
            #         reasoning_model=REASONING_DIFFICULTY_MODEL,
            #         non_reasoning_model=BASE_MODEL,
            #         display=config.display,
            #         epochs=1,
            #         testing_scheme=TESTING_SCHEME,
            #         log_dir=TOP_LEVEL_LOG_DIR,
            #         temperature=TEMPERATURE,
            #         max_connections=MAX_CONNECTIONS,
            #     )

            #     if reasoning_accuracy < 1:
            #         excluded_behaviors.append(behavior)
            #         continue

            (
                p_acknowledged_clue,
                p_take_hints,
                faithfulness_stderr,
                completed_samples,
            ) = get_free_response_faithfulness_score(
                dataset,
                behavior,
                model=MODEL,
                max_connections=MAX_CONNECTIONS,
                limit=100,
                display=config.display,
                log_dir=TOP_LEVEL_LOG_DIR,
                temperature=TEMPERATURE,
            )
        # else:
        #     (
        #         reasoning_accuracy,
        #         non_reasoning_accuracy,
        #         reasoning_stderr,
        #         non_reasoning_stderr,
        #     ) = get_clue_difficulty(
        #         behavior,
        #         reasoning_model=REASONING_DIFFICULTY_MODEL,
        #         non_reasoning_model=BASE_MODEL,
        #         display=config.display,
        #         epochs=10,
        #         testing_scheme=TESTING_SCHEME,
        #         log_dir=TOP_LEVEL_LOG_DIR,
        #         temperature=TEMPERATURE,
        #         max_connections=MAX_CONNECTIONS,
        #     )

        #     (
        #         p_acknowledged_clue,
        #         p_take_hints,
        #         faithfulness_stderr,
        #         completed_samples,
        #     ) = get_faithfulness_score(
        #         behavior,
        #         model=MODEL,
        #         max_connections=MAX_CONNECTIONS,
        #         limit=100,
        #         display=config.display,
        #         log_dir=TOP_LEVEL_LOG_DIR,
        #         temperature=TEMPERATURE,
        #     )

        # reasoning_accuracies.append(reasoning_accuracy)
        # non_reasoning_accuracies.append(non_reasoning_accuracy)
        # difficulty_scores.append(1 - non_reasoning_accuracy)
        # difficulty_stderrs.append(non_reasoning_stderr)
        faithfulness_scores.append(p_acknowledged_clue)
        faithfulness_stderrs.append(faithfulness_stderr)
        take_hints_scores.append(p_take_hints)
        samples.append(completed_samples)

        # generate_with_and_without_cot_difficulty_graph(
        #     reasoning_accuracies,
        #     non_reasoning_accuracies,
        #     [case.value for case in cases if case not in excluded_behaviors],
        #     MODEL,
        #     dataset_name,
        # )

        # generate_propensity_graph(
        #     faithfulness_scores,
        #     faithfulness_stderrs,
        #     difficulty_scores,
        #     difficulty_stderrs,
        #     labels=[case.value for case in cases if case not in excluded_behaviors],
        #     model=MODEL,
        #     dataset=dataset_name,
        #     show_labels=False,
        # )

    # save faithfulness scores to json, custom code for grey swan
    import json

    faithfulness_scores_dict = {}
    for i in range(len(cases)):
        faithfulness_scores_dict[cases[i].value] = faithfulness_scores[i]

    with open("faithfulness_scores.json", "w") as f:
        json.dump(faithfulness_scores_dict, f)

    generate_taking_hints_graph(
        take_hints_scores,
        labels=[case.value for case in cases if case not in excluded_behaviors],
        model=MODEL,
        dataset=dataset_name,
    )

    # generate_taking_hints_v_difficulty_graph(
    #     take_hints_scores,
    #     difficulty_scores,
    #     labels=[case.value for case in cases if case not in excluded_behaviors],
    #     model=MODEL,
    #     dataset=dataset_name,
    # )
