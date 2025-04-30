# METR Faithfulness Eval

This is an evaluation designed to test faithfulness in LLM CoTs.

## Usage

The entry point is `src/main.py`.

```bash
python src/main.py
```

The file takes a few arguments:

- `--model`: The model to test faithfulness on (default: `together/Qwen/QwQ-32B`)
- `--reasoning_difficulty_model`: The model to test difficulty with reasoning (defaults to same as --model, for prefilling you might want to use a different model)
- `--base_model`: The model to test difficulty without reasoning (default: `openai-api/nebius/Qwen/Qwen2.5-32B-Instruct`) 
- `--display`: Display mode for evaluation progress (default: `none`, other options are `full`)
- `--testing_scheme`: Testing scheme to use, one of: `base`, `rl_no_reasoning`, `rl_dots` (default: `base`)
- `--redteam`: Run evaluation on a subset of test cases, store_true

## Output

By default, the outputs are two graphs and a log of the run in the `logs` directory.