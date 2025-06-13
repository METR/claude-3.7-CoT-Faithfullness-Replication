# METR Faithfulness Eval

This is an evaluation designed to test faithfulness in LLM CoTs.

## Usage

The entry point is `src/main.py`.
```bash
python src/main.py
```

### Arguments
- `model`: the model to test faithfulness on (defaults to `anthropic/claude-3-7-sonnet-latest`)
- `reasoning_difficulty_model`: the model to test difficulty with reasoning (defaults to same as `model`). we sometimes want to be able to use different providers for this model
- `base_model`: the model to test difficulty without reasoning (defaults to `anthropic/claude-3-7-sonnet-latest`)
- `display`: display mode for evaluation progress (`none` or `full`, default: `none`) (this currently doesn't work)
- `testing_scheme`: testing scheme to use (`base`, `rl_no_reasoning`, or `rl_dots`, default: `base`)
- `redteam`: run evaluation on a subset of test cases (flag, no value needed)
- `temperature`: temperature parameter for model generation (default: 0.6)
- `max_connections`: maximum number of concurrent requests to model providers (default: 30)
- `filtered_csv`: path to CSV file with pre-computed difficulty scores. if not provided, will recompute scores.
- `prompt_file`: path to prompt file (defaults to `utils/prompts/default.py`)
  

## Output

By default, the outputs are two graphs and a log of the run in the `logs` directory.