from behaviors import FUNCTION_DICT
from tqdm import tqdm
from clue_difficulty import get_clue_difficulty, TestingScheme
import argparse
from llm_faithfulness import get_faithfulness_score
from fr_faithfulness import get_fr_faithfulness_score
from graph_utils import (
    generate_propensity_graph,
    generate_taking_hints_graph,
    generate_taking_hints_v_difficulty_graph,
    generate_with_and_without_cot_difficulty_graph,
)
from os import path
from datetime import datetime
from parsing import parse_args


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
    EVAL_TYPE: str = config.eval_type

    faithfulness_scores = []
    faithfulness_stderrs = []
    difficulty_scores = []
    difficulty_stderrs = []
    reasoning_accuracies = []
    non_reasoning_accuracies = []
    delta_scores = []
    samples = []
    ic_counts = []
    i_star_counts = []

    cases = list(FUNCTION_DICT.keys())
    if REDTEAM:
        cases = cases[::3]  # Take every 3rd element

    evaled_cases = []

    for behavior in tqdm(cases):
        (
            reasoning_accuracy,
            non_reasoning_accuracy,
            reasoning_stderr,
            non_reasoning_stderr,
        ) = get_clue_difficulty(
            behavior,
            reasoning_model=REASONING_DIFFICULTY_MODEL,
            non_reasoning_model=BASE_MODEL,
            display=config.display,
            epochs=10,
            testing_scheme=TESTING_SCHEME,
            log_dir=TOP_LEVEL_LOG_DIR,
            temperature=TEMPERATURE,
            max_connections=MAX_CONNECTIONS,
        )

        if EVAL_TYPE == "multiple_choice":
            (
                faithful_score,
                faithful_stderr,
                delta_correctness,
                completed_samples,
                ic_count,
                i_star_count,
            ) = get_faithfulness_score(
                behavior,
                model=MODEL,
                max_connections=MAX_CONNECTIONS,
                limit=100,
                display=config.display,
                log_dir=TOP_LEVEL_LOG_DIR,
                temperature=TEMPERATURE,
            )
        else:
            (
                faithful_score,
                faithful_stderr,
                delta_correctness,
                completed_samples,
                ic_count,
                i_star_count,
            ) = get_fr_faithfulness_score(
                behavior,
                model=MODEL,
                max_connections=MAX_CONNECTIONS,
                limit=100,
                display=config.display,
                log_dir=TOP_LEVEL_LOG_DIR,
                temperature=TEMPERATURE,
            )

        if faithful_score is None:
            print(f"Skipping {behavior} because it's not in the FR dataset")
            continue

        take_hints = ic_count / i_star_count
        faithfulness_scores.append(faithful_score)
        faithfulness_stderrs.append(faithful_stderr)
        reasoning_accuracies.append(reasoning_accuracy)
        non_reasoning_accuracies.append(non_reasoning_accuracy)
        difficulty_scores.append(1 - non_reasoning_accuracy)
        difficulty_stderrs.append(non_reasoning_stderr)
        delta_scores.append(delta_correctness)
        samples.append(completed_samples)
        ic_counts.append(ic_count)
        i_star_counts.append(i_star_count)
        evaled_cases.append(behavior)
    generate_with_and_without_cot_difficulty_graph(
        reasoning_accuracies,
        non_reasoning_accuracies,
        [case.value for case in evaled_cases],
        MODEL,
    )

    generate_propensity_graph(
        faithfulness_scores,
        faithfulness_stderrs,
        difficulty_scores,
        difficulty_stderrs,
        labels=[case.value for case in evaled_cases],
        model=MODEL,
        testing_scheme=TESTING_SCHEME,
        show_labels=False,
    )

    generate_taking_hints_graph(
        i_star_counts,
        ic_counts,
        labels=[case.value for case in evaled_cases],
        model=MODEL,
    )

    generate_taking_hints_v_difficulty_graph(
        i_star_counts,
        delta_scores,
        difficulty_scores,
        labels=[case.value for case in evaled_cases],
        model=MODEL,
    )
