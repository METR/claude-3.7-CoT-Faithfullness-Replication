@scorer(metrics=[accuracy(), stderr()])
def choice() -> Scorer:
    """
    Scorer for multiple choice answers, required by the `multiple_choice` solver.

    This assumes that the model was called using a template ordered with letters
    corresponding to the answers, so something like:

        What is the capital of France?

        A) Paris
        B) Berlin
        C) London

    The target for the dataset will then have a letter corresponding to the
    correct answer, e.g. the `Target` would be `"A"` for the above question. If
    multiple choices are correct, the `Target` can be an array of these letters.
    """

    async def score(state: TaskState, target: Target) -> Score:
        choices = state.choices

        if _choices_are_shuffled(choices):
            explanation = _shuffled_explanation(choices)
            # Unshuffle the choices so that we can score them correctly against
            # the target
            choices = unshuffle_choices(choices)
        else:
            explanation = state.output.completion

        target_positions, answers = _score_target(target, choices)

        generated_selected_choices = [
            i for i, choice in enumerate(choices) if choice.correct is True
        ]

        target_matches_choices = generated_selected_choices == sorted(target_positions)

        return Score(
            value=CORRECT if target_matches_choices else INCORRECT,
            answer=", ".join(answers),
            explanation=explanation,
        )

    return score