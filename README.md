# METR Faithfulness Eval

This is an evaluation designed to test faithfulness in Language Model Chains of Thought (CoTs)

## Usage

The entrypoint for this repo is `src/graph.py`.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the evaluation:

```bash
python src/graph.py --model <model_name> --base_model <base_model_name>
```

By default (i.e, when run with no parameters), this defaults to running the evaluation with `together/Qwen/QwQ-32B` as the reasoning model and `Nebius/Qwen2.5-32B-instruct` as the base model. As far as I can tell, Nebius is the only provider that hosts `Qwen2.5-32B-instruct`. 

In order to use it, set API keys in your `.env` file for your respective providers. More instructions on setup can be found at the [InspectAI docs](https://inspect.aisi.org.uk/#getting-started)

## Method

The evaluation follows the methology of the Claude 3.7 Sonnet model card closely. However, we also measure the difficulty of clues by how much better a model with Chain of Thought reasoning is at solving the clue compared to a model without Chain of Thought reasoning. This quantifies how important Chain of Thought reasoning is for a given clue. 
