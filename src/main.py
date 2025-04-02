from inspect_ai import eval
from llm_faithfulness import llm_faithfulness
from behaviors import Behavior

"""
TODO:
- [ ] Make this a streamlined script to run evals
"""

"""
This script is used to run evals on the model. 

"""


def main():
    eval(
        llm_faithfulness(clue=Behavior.REWARD_HACKING.value, limit=100),
        model="together/Qwen/QwQ-32B",
    )
    eval(
        llm_faithfulness(clue=Behavior.SYNCOPHANTIC.value, limit=100),
        model="together/Qwen/QwQ-32B",
    )
    eval(
        llm_faithfulness(clue=Behavior.XOR_ENCRYPT.value, limit=100),
        model="together/Qwen/QwQ-32B",
    )
    eval(
        llm_faithfulness(clue=Behavior.OBFUSCATED.value, limit=100),
        model="together/Qwen/QwQ-32B",
    )
    eval(
        llm_faithfulness(clue=Behavior.BASE64_SLICE.value, limit=100),
        model="together/Qwen/QwQ-32B",
    )
    eval(
        llm_faithfulness(clue=Behavior.NESTED_INDEX.value, limit=100),
        model="together/Qwen/QwQ-32B",
    )


if __name__ == "__main__":
    main()
