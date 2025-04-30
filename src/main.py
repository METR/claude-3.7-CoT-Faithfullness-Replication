from behaviors import FUNCTION_DICT
from tqdm import tqdm
from clue_difficulty import get_clue_difficulty, TestingScheme
import argparse
from llm_faithfulness import get_faithfulness_score
from graph_utils import generate_propensity_graph, generate_taking_hints_graph
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

    faithfulness_scores = []
    faithfulness_stderrs = []
    difficulty_scores = []
    difficulty_stderrs = []
    delta_scores = []
    samples = []
    ic_counts = []
    i_star_counts = []

    cases = list(FUNCTION_DICT.keys())
    if REDTEAM:
        cases = cases[::4]  # Take every 4th element

    for behavior in tqdm(cases):
        diff, diff_stderr = get_clue_difficulty(
            behavior,
            reasoning_model=REASONING_DIFFICULTY_MODEL,
            non_reasoning_model=BASE_MODEL,
            display=config.display,
            epochs=10,
            testing_scheme=TESTING_SCHEME,
            log_dir=TOP_LEVEL_LOG_DIR,
        )

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
            max_connections=100,
            limit=100,
            display=config.display,
            log_dir=TOP_LEVEL_LOG_DIR,
        )

        faithfulness_scores.append(faithful_score)
        faithfulness_stderrs.append(faithful_stderr)
        difficulty_scores.append(diff)
        difficulty_stderrs.append(diff_stderr)
        delta_scores.append(delta_correctness)
        samples.append(completed_samples)
        ic_counts.append(ic_count)
        i_star_counts.append(i_star_count)

    generate_propensity_graph(
        faithfulness_scores,
        faithfulness_stderrs,
        difficulty_scores,
        difficulty_stderrs,
        labels=[case.value for case in cases],
        model=MODEL,
        testing_scheme=TESTING_SCHEME,
        show_labels=False,
    )

    generate_taking_hints_graph(
        i_star_counts,
        ic_counts,
        labels=[case.value for case in cases],
        model=MODEL,
    )
