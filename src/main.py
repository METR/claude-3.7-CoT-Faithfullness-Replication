from free_response_behaviors import FR_FUNCTION_DICT
from tqdm import tqdm
from graph_utils import (
    save_raw_data_to_json,
)
from datetime import datetime
from parsing import parse_args
from free_response_clue_difficulty import get_free_response_clue_difficulty
from free_response_llm_faithfulness import get_free_response_faithfulness_score
from filtering import get_problem_difficulty
from utils.prompt_utils import load_prompt_module
from utils.question_prompts.default import DEFAULT_QUESTION_PREFIX

from typing import List

if __name__ == "__main__":
    config = parse_args()

    TOP_LEVEL_LOG_DIR: str = f"./logs/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{config.model.replace('/', '-')}-{config.testing_scheme.value}/"
    RAW_DATA_PATH: str = f"./results/faithfulness/{datetime.now().strftime('%Y%m%d-%H%M%S')}-{config.model.replace('/', '-')}.json"
    PROMPT_MODULE = load_prompt_module(config.question_prompt)
    QUESTION_PREFIX = PROMPT_MODULE.QUESTION_PREFIX
    QUESTION_SUFFIX = PROMPT_MODULE.QUESTION_SUFFIX
    HINT_SUFFIX = PROMPT_MODULE.HINT_SUFFIX
    JUDGE_PROMPT = load_prompt_module(config.judge_prompt).JUDGE_PROMPT

    faithfulness_scores: List[float] = []
    faithfulness_stderrs: List[float] = []
    difficulty_scores: List[float] = []
    difficulty_stderrs: List[float] = []
    reasoning_accuracies: List[float] = []
    non_reasoning_accuracies: List[float] = []
    take_hints_scores: List[float] = []
    samples: List[int] = []

    cases = list(FR_FUNCTION_DICT.keys())
    dataset_name = "metr/hard-math"

    dataset, _ = get_problem_difficulty(
        reasoning_model=config.model,
        display=config.display,
        epochs=5,
        log_dir=TOP_LEVEL_LOG_DIR,
        temperature=config.temperature,
        max_connections=config.max_connections,
        limit=200,
        filtered_csv=config.filtered_csv,
        prompt_template=DEFAULT_QUESTION_PREFIX,
    )
    excluded_behaviors = []

    for behavior in tqdm(cases):
        # (
        #     reasoning_accuracy,
        #     non_reasoning_accuracy,
        #     reasoning_stderr,
        #     non_reasoning_stderr,
        # ) = get_free_response_clue_difficulty(
        #     behavior,
        #     reasoning_model=config.reasoning_difficulty_model,
        #     non_reasoning_model=config.base_model,
        #     display=config.display,
        #     epochs=1,
        #     testing_scheme=config.testing_scheme,
        #     log_dir=TOP_LEVEL_LOG_DIR,
        #     temperature=config.temperature,
        #     max_connections=config.max_connections,
        # )

        # if reasoning_accuracy < 0.95:
        #     excluded_behaviors.append(behavior)
        #     continue

        (
            p_acknowledged_clue,
            p_take_hints,
            faithfulness_stderr,
            completed_samples,
        ) = get_free_response_faithfulness_score(
            dataset,
            behavior,
            model=config.model,
            max_connections=config.max_connections,
            limit=100,
            display=config.display,
            log_dir=TOP_LEVEL_LOG_DIR,
            temperature=config.temperature,
            prompt_prefix=QUESTION_PREFIX,
            prompt_suffix=QUESTION_SUFFIX,
            hint_suffix=HINT_SUFFIX,
            judge_prompt=JUDGE_PROMPT,
            score_faithfulness=config.score_faithfulness,
        )
        # reasoning_accuracies.append(reasoning_accuracy)
        # non_reasoning_accuracies.append(non_reasoning_accuracy)
        # difficulty_scores.append(1 - non_reasoning_accuracy)
        # difficulty_stderrs.append(non_reasoning_stderr)
        faithfulness_scores.append(p_acknowledged_clue)
        faithfulness_stderrs.append(faithfulness_stderr)
        take_hints_scores.append(p_take_hints)
        samples.append(completed_samples)

    labels = [case.value for case in cases if case not in excluded_behaviors]
    save_raw_data_to_json(
        labels,
        reasoning_accuracies,
        non_reasoning_accuracies,
        difficulty_scores,
        difficulty_stderrs,
        faithfulness_scores,
        faithfulness_stderrs,
        take_hints_scores,
        samples,
        RAW_DATA_PATH,
    )
