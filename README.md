Quick and dirty replication of the LLM faithfulness eval from Anthropic's Claude 3.7 Sonnet model card.

Run with `inspect-ai` !

```
inspect eval llm_faithfulness.py --model <model> -T clue=<clue>
```

For example:

```
inspect eval llm_faithfulness.py --model together/Qwen/QwQ-32B -T clue=reward_hacking
```

