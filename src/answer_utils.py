from typing import Any

from inspect_ai.dataset import Sample


def answer_index(char: str) -> int:
    r"""
    Helper to go from char to array index, for example:

        'A' -> 0, 'B' -> 1, etc
    """
    return ord(char.upper()) - ord("A")


def answer_character(index: int) -> str:
    r"""
    Helper to go from array index to char, for example:

        0 -> 'A', 1 -> 'B', etc
    """
    return chr(ord("A") + index)


def answer_options(choices) -> str:
    r"""
    Returns the `choices` formatted as a multiple choice question, e.g.:

    ["choice 1", "choice 2", "choice 3"] ->
        "A) choice 1\nB) choice 2\nC) choice 3"
    """
    indexes = list(range(len(choices)))

    return "\n".join(
        [f"{chr(65 + i)}) {choices[j].value}" for i, j in enumerate(indexes)]
    )


def set_choices_based_on_generated_response(state, answers: str) -> None:
    """
    Set the choices based on the generated response
    """
    true_answers = [answer_index(letter) for letter in answers]

    for i in range(len(state.choices)):
        if i in true_answers:
            state.choices.mark_choice(i, True)
        else:
            state.choices.mark_choice(i, False)


def record_to_sample(record: dict[str, Any]) -> Sample:
    """
    Convert a record to a sample
    """
    return Sample(
        input=record["Question"],
        choices=[
            str(record["Correct Answer"]),
            str(record["Incorrect Answer 1"]),
            str(record["Incorrect Answer 2"]),
            str(record["Incorrect Answer 3"]),
        ],
        target="A",
        id=record["Record ID"],
    )
