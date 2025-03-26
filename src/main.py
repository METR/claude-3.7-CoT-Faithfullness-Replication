from inspect_ai import eval
from llm_faithfulness import llm_faithfulness

"""
TODO:
- [ ] Make this a streamlined script to run evals
"""

"""
This script is used to run evals on the model. 

"""


def main():
    eval(
        llm_faithfulness(clue="xor_encrypt", limit=100),
        model="together/Qwen/QwQ-32B",
    )
    ...


if __name__ == "__main__":
    main()
