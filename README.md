# METR Faithfulness and Monitorability Experiments

This is an evaluation designed to test under what circumstances LLMs' CoTs might be faithful and monitorable.

## Usage

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

---

## Monitorability False Positive Evaluation

This codebase also evaluates the **false positive rate** of the monitor/monitorability prompt on a control set of questions where the model solves the problem without a hint.

- This is run automatically at the end of `src/main.py` and outputs results to `logs/<timestamp>/monitor_control_results.json`.
- You can also run it standalone:

```bash
python src/monitor_control_eval.py --model <model_name> --judge_prompt <path_to_monitorability_prompt>
```

- The output JSON includes, for each question, the number of correct runs, number of false positives (cases where the monitor incorrectly flagged a correct/no-hint run as using a hint), and the false positive rate. It also reports the overall false positive rate across all control runs.

This allows you to measure how often the monitorability prompt incorrectly flags normal, correct model behavior as suspicious (i.e., the fast positive rate of the monitor on non-hint questions).
