import json
import os
from datetime import datetime
from typing import Any, List, Tuple

from src.parsing import EvalConfig


def get_latest_json_file(json_files: List[str]) -> dict[str, Any] | None:
    if json_files:
        # Extract datetime strings from filenames and find the latest
        datetime_files: List[Tuple[str, str]] = []
        for file_path in json_files:
            filename = os.path.basename(file_path)
            if filename.endswith(".json"):
                datetime_str = filename[:15]  # first 15 chars are the datetime str
                try:
                    # Parse the datetime string to validate it
                    datetime.strptime(datetime_str, "%Y%m%d-%H%M%S")
                    datetime_files.append((datetime_str, file_path))
                except ValueError:
                    # Skip files that don't match the datetime pattern
                    continue

        if datetime_files:
            # Sort by datetime string and get the latest
            datetime_files.sort(key=lambda x: x[0], reverse=True)
            latest_file_path = datetime_files[0][1]

            with open(latest_file_path, "r") as f:
                data = json.load(f)
                # Process the data as needed
                return data
        else:
            print(f"No valid datetime-formatted JSON files found.")
            return None
    else:
        print(f"No JSON files found.")
        return None


def save_clue_difficulty_data_to_json(
    config: EvalConfig,
    labels: List[str],
    reasoning_accuracies: List[float],
    non_reasoning_accuracies: List[float],
    difficulty_scores: List[float],
    difficulty_stderrs: List[float],
    path: str,
) -> None:
    data = {
        "metadata": {
            "model": config.model,
            "base_model": config.base_model,
            "testing_scheme": config.testing_scheme.value,
            "temperature": config.temperature,
            "question_prompt": config.question_prompt,
            "judge_prompt": config.judge_prompt,
            "score_faithfulness": config.score_faithfulness,
            "test_monitor_false_positives": config.test_monitor_false_positives,
        },
        "labels": labels,
        "reasoning_accuracies": reasoning_accuracies,
        "non_reasoning_accuracies": non_reasoning_accuracies,
        "difficulty_scores": difficulty_scores,
        "difficulty_stderrs": difficulty_stderrs,
    }
    with open(path, "w") as f:
        json.dump(data, f)
