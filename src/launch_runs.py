#!/usr/bin/env python3

import os
import subprocess
import time

# Base configuration
BATCH_SIZE = 2000

# Define temperatures for each model
model_temperatures = {
    "anthropic/claude-3-7-sonnet-latest": 1,
    "anthropic/claude-opus-4-20250514": 1,
    "together/Qwen/Qwen3-235B-A22B-fp8-tput": 0.6,
}

# Define models and their corresponding CSV files
models = {
    "anthropic/claude-3-7-sonnet-latest": "problem_difficulty/claude-3-7-sonnet-latest_hard-math-v0_difficulty.csv",
    "anthropic/claude-opus-4-20250514": "problem_difficulty/claude-opus-4-20250514_hard-math-v0_difficulty.csv",
    "together/Qwen/Qwen3-235B-A22B-fp8-tput": "problem_difficulty/Qwen3-235B-A22B-fp8-tput_hard-math-v0_difficulty.csv",
}

# Define model short names for session naming
model_short_names = {
    "anthropic/claude-3-7-sonnet-latest": "c3.7s",
    "anthropic/claude-opus-4-20250514": "opus4",
    "together/Qwen/Qwen3-235B-A22B-fp8-tput": "qwen3-235b",
}

# Define combinations for each model (question_prompt, judge_prompt)
model_combinations = {
    "anthropic/claude-3-7-sonnet-latest": [
        "default.py,faithfulness_2_broad_definition.py",
        "moe_v4.py,faithfulness_2_broad_definition.py",
        "moe_v4.py,faithfulness_0611.py",
        "moe_v4.py,monitorability_0624.py",
        "grug.py,faithfulness_2_broad_definition.py",
        "grug.py,faithfulness_0611.py",
        "grug.py,monitorability_0624.py",
        "cheater_ai.py,faithfulness_2_broad_definition.py",
        "cheater_ai.py,monitorability_0624.py",
        "general_instructive.py,faithfulness_2_broad_definition.py",
        "general_instructive.py,monitorability_0624.py",
        "tcgs_non_instructive.py,faithfulness_2_broad_definition.py",
        "tcgs_non_instructive.py,monitorability_0624.py",
    ],
    "anthropic/claude-opus-4-20250514": [
        "default.py,faithfulness_2_broad_definition.py",
        "moe_v4.py,faithfulness_2_broad_definition.py",
        "moe_v4.py,faithfulness_0611.py",
        "moe_v4.py,monitorability_0624.py",
        "grug.py,faithfulness_2_broad_definition.py",
        "grug.py,faithfulness_0611.py",
        "grug.py,monitorability_0624.py",
        "cheater_ai.py,faithfulness_2_broad_definition.py",
        "cheater_ai.py,monitorability_0624.py",
        "general_instructive.py,faithfulness_2_broad_definition.py",
        "general_instructive.py,monitorability_0624.py",
        "tcgs_non_instructive.py,faithfulness_2_broad_definition.py",
        "tcgs_non_instructive.py,monitorability_0624.py",
    ],
    "together/Qwen/Qwen3-235B-A22B-fp8-tput": [
        "moe_v4.py,faithfulness_2_broad_definition.py",
        "moe_v4.py,monitorability_0624.py",
        "cheater_ai.py,faithfulness_2_broad_definition.py",
        "cheater_ai.py,monitorability_0624.py",
    ],
}


def launch_screen_session(session_name: str, command: str) -> bool:
    """Launch a command in a screen session."""
    screen_cmd = [
        "screen",
        "-dmS",
        session_name,
        "bash",
        "-c",
        f"{command}; echo 'Command finished with exit code: $?'; read -p 'Press Enter to close...'",
    ]

    try:
        subprocess.run(screen_cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error launching session {session_name}: {e}")
        return False


def main():
    print("Launching runs in screen sessions...")

    # Loop through each model
    for model, filtered_csv in models.items():
        if model not in model_combinations:
            print(f"Warning: No combinations defined for model {model}, skipping...")
            continue

        model_short = model_short_names.get(
            model, model.replace("/", "-").replace(".", "")
        )

        print(f"Starting runs for model: {model}")
        print(f"Using CSV: {filtered_csv}")
        print("")

        # Get temperature for this model
        temperature = model_temperatures.get(model, 1)  # Default to 1 if not specified

        # Loop through each combination for this model
        for combo in model_combinations[model]:
            question_prompt, judge_prompt = combo.split(",")

            # Remove .py extension for screen session naming
            question_short = os.path.splitext(os.path.basename(question_prompt))[0]
            judge_short = os.path.splitext(os.path.basename(judge_prompt))[0]

            # Create screen session name: model-question-judge
            session_name = f"{model_short}-{question_short}-{judge_short}"

            # Check if judge prompt contains "monitorability" to determine score_faithfulness flag
            score_faithfulness_flag = ""
            if "monitorability" not in judge_prompt:
                score_faithfulness_flag = "--score_faithfulness"

            # Build the full command
            cmd_parts = [
                "python main_faithfulness.py",
                f"--model {model}",
                f"--base_model {model}",
                f"--batch_size {BATCH_SIZE}",
                f"--temperature {temperature}",
                f"--filtered_csv {filtered_csv}",
                "--max_tasks 50",
                f"--question_prompt utils/question_prompts/{question_prompt}",
                f"--judge_prompt utils/judge_prompts/{judge_prompt}",
            ]

            if score_faithfulness_flag:
                cmd_parts.append(score_faithfulness_flag)

            cmd = " ".join(cmd_parts)

            print(f"Starting session: {session_name}")
            print(f"Command: {cmd}")
            print("---")

            # Launch in screen session
            success = launch_screen_session(session_name, cmd)
            if not success:
                print(f"Failed to start session: {session_name}")
                continue

            # Small delay to avoid overwhelming the system
            time.sleep(1)

        print(f"Completed launching sessions for {model}")
        print("-------------------------------------")
        print("")

    print("All sessions started!")
    print("Use 'screen -ls' to see active sessions")
    print("Use 'screen -r <session_name>' to attach to a session")


if __name__ == "__main__":
    main()
