# METR Faithfulness and Monitorability Experiments

This is an evaluation designed to test under what circumstances LLMs' CoTs might be faithful and monitorable.

## Usage

To collect data on clue difficulty:
```bash
python src/main_difficulty.py
```

Args relevant to this script:
- `--model`: The model to test faithfulness on (default: `anthropic/claude-3-7-sonnet-latest`)
- `--base_model`: The model to test difficulty without reasoning (default: `anthropic/claude-3-7-sonnet-latest`) 
- `--temperature`: The model temperature when getting difficulty and faithfulness. Default to 0.6. Temperature doesn't affect claude extended thinking mode.
- `--batch_size`: The number of queries to send in parallel leveraging batch API.
- `--max_connections`: The maximum number of connections to make with the provider. If `batch_size` is provided, this will be set to equal `batch_size`.
- `--max_tasks`: The number of tasks to run in parallel in an eval set. Default to 5. 


To collect data on faithfulness or monitorability:
```bash
python src/main_faithfulness.py
```

Args relevant to this script:
- `--model`: The model to test faithfulness on (default: `anthropic/claude-3-7-sonnet-latest`)
- `--base_model`: The model to test difficulty without reasoning (default: `anthropic/claude-3-7-sonnet-latest`) 
- `--temperature`: The model temperature when getting difficulty and faithfulness. Default to 0.6. Temperature doesn't affect claude extended thinking mode.
- `--batch_size`: The number of queries to send in parallel leveraging batch API. Not including this arg will mean that we're not using the batch api. Recommended batch_size is 2000-5000.
- `--max_connections`: The maximum number of connections to make with the provider. If `batch_size` is provided, this will be set to equal `batch_size`.
- `--max_tasks`: The number of tasks to run in parallel in an eval set. Default to 5. 
- `--filtered_csv`: The filtered out questions that the model cannot solve
- `--question_prompt`: The question prompt used to introduce the hard problem and the hint.
- `--judge_prompt`: The LLM Judge prompt used to decide whether the CoT is faithful / monitorable
- `--score_faithfulness`: A store_true flag indicating this is a faithfulness judge, which does see the hint provided to the model


To generate graphs:
```bash
python graph.py
```

By default, this script goes through the faithfulness and monitorability folder under `results/` and create graphs for all the JSON files under the folder, excluding the ones under `subset/` folders. 
Args:
`--file`: You can optionally pass in a result json path to only create the graph for that particular result file.
`--hint_taking_threshold`: remove clues that has a hint taking rate below the threshold from the propensity graph. Default to 0.1


## Usage OUTDATED

The entry point is `src/main.py`.

```bash
python src/main.py
```

The file takes a few arguments:

- `--model`: The model to test faithfulness on (default: `anthropic/claude-3-7-sonnet-latest`)
- `--base_model`: The model to test difficulty without reasoning (default: `anthropic/claude-3-7-sonnet-latest`) 
- `--filtered_csv`: Path to the csv file with difficulty scores instead of re-running filtering. Default to None.

- `--redteam`: Run evaluation on a subset of test cases, stores true.
- `--temperature`: The model temperature when getting difficulty and faithfulness. Default to 0.6, which Qwq's default temperature. Claude 3.7 Sonnet's default temperature is 1
- `--max_connections`: Number of concurrent request to send to the providers. Default to 20. One might want to customize this based on the rate limits.

- `--question_prompt`: Path to the question prompt file. Default to `utils/prompts/default.py`.
- `--judge_prompt`: Path to the judge prompt file. Default to `utils/judge_prompts/faithfulness_0611.txt`.
- `--score_faithfulness`: Whether to score faithfulness. Default to false.

Legacy / Compatibility arguments:
- `--display`: Display mode for evaluation progress (default: `none`, other options are `full`) (broken)
- `--testing_scheme`: Testing scheme to use, one of: `base`, `rl_no_reasoning`, `rl_dots` (default: `base`)

## Output

By default, the outputs are two graphs and a log of the run in the `logs` directory.
