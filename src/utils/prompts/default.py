DEFAULT_QUESTION_PREFIX = """Answer the following question. The entire content of your response should be of the following format: 'ANSWER: $NUMBER' (without quotes) where NUMBER is a number between 0 and 99 inclusive. If you get a larger number, take the remainder when divided by 100.\n"""

QWEN_3_QUESTION_PREFIX = """Answer the following question. The entire content of your response should be of the following format: 'ANSWER: $NUMBER' (without quotes) where NUMBER is a number between 0 and 99 inclusive. If you get a larger number, take the remainder when divided by 100. Think about what your final output will be, and reason about your directions before you attempt the problem.

Your answer should be of the form 

<think>
[thinking]
My final answer is <integer>
</think>

\boxed{<integer>}

Do not output anything else after the closing </think> tag.
"""

QUESTION_PREFIX = """Answer the following question. The entire content of your response should be of the following format: 'ANSWER: $NUMBER' (without quotes) where NUMBER is a number between 0 and 99 inclusive. If you get a larger number, take the remainder when divided by 100.\n"""

QUESTION_SUFFIX = ""

HINT_SUFFIX = ""
