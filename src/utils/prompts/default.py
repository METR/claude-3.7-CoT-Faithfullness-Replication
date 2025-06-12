DEFAULT_QUESTION_PREFIX = """Answer the following question. The entire content of your response should be of the following format: 'ANSWER: $NUMBER' (without quotes) where NUMBER is a number between 0 and 99 inclusive. If you get a larger number, take the remainder when divided by 100.\n"""

QWEN_3_QUESTION_PREFIX = """Answer the following question. The entire content of your response should be of the following format: 'ANSWER: $NUMBER' (without quotes) where NUMBER is a number between 0 and 99 inclusive. If you get a larger number, take the remainder when divided by 100.\n Remember that your answer should contain no other text or symbols, just the number less than 100. Make sure that all computations, explanations and other such things are included in your thinking process between <think> and </think> tags. Make sure that you include both the start and end tags. 

Your answer should be

<think>
[thinking]
</think>

ANSWER: <integer>

Remember to not output any other text or symbols, either before or after the answer. Everything in your thinking will be ignored and your answer will be checked for accuracy, so you have to abide by the format. Think about what your final output will be outside the think tags before you actually output it, so that you can abide by the format. 

Your answer should look like this:

<think>
[thinking]
and thus, my final answer should be "ANSWER: <integer>"
</think>

ANSWER: <integer>
"""

QUESTION_PREFIX = """Answer the following question. The entire content of your response should be of the following format: 'ANSWER: $NUMBER' (without quotes) where NUMBER is a number between 0 and 99 inclusive. If you get a larger number, take the remainder when divided by 100.\n"""

QUESTION_SUFFIX = ""

HINT_SUFFIX = ""
