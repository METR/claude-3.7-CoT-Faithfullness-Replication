# METR Faithfulness Eval

This is an evaluation designed to test faithfulness in LLM CoTs.

## Usage

The entry point is `src/main.py`.
```bash
python src/main.py
```

### Arguments
- `--model`: The model to test faithfulness on (default: `together/Qwen/QwQ-32B`)
- `--reasoning_difficulty_model`: The model to test difficulty with reasoning (defaults to same as --model). For prefilling, you may want to use a different model than the main model.
- `--base_model`: The model to test difficulty without reasoning (default: `openai-api/nebius/Qwen/Qwen2.5-32B-Instruct`)
- `--display`: Display mode for evaluation progress (`none` or `full`, default: `none`)
- `--testing_scheme`: Testing scheme to use (`base`, `rl_no_reasoning`, or `rl_dots`, default: `base`)
- `--redteam`: Run evaluation on a subset of test cases (flag, no value needed)
- `--temperature`: Temperature parameter for model generation. Default is 0.6 (Qwen's default). Note that different models may have different optimal temperatures (e.g. Claude 3.7 Sonnet uses 1.0 by default)
- `--max_connections`: Maximum number of concurrent requests to model providers. Default is 20. Adjust based on provider rate limits.
- `--filtered_csv`: Path to CSV file with pre-computed difficulty scores. If not provided, will recompute scores.
- `--boxplot_lower_threshold`: Lower threshold for boxplot visualization (default: 0.2)
- `--boxplot_upper_threshold`: Upper threshold for boxplot visualization (default: 0.8)
- `--prompt_fp`: Path to prompts file (default: `utils/prompts/default.py`)
  

## Output

By default, the outputs are two graphs and a log of the run in the `logs` directory.