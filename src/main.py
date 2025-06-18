import os
import time
import traceback
from dotenv import load_dotenv

from parsing import parse_args
from evaluation import Evaluator
from graph_utils import save_raw_data_to_json


def run_once():
    """Run a single evaluation pipeline."""
    # Load environment variables
    load_dotenv()
    
    # Verify API key is present
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is required")

    # Parse command line arguments
    config = parse_args()

    # Run evaluation
    evaluator = Evaluator(config)
    results = evaluator.run_evaluation()

    # Save results
    save_raw_data_to_json(
        config=config,
        labels=results.labels,
        reasoning_accuracies=results.reasoning_accuracies,
        non_reasoning_accuracies=results.non_reasoning_accuracies,
        difficulty_scores=results.difficulty_scores,
        difficulty_stderrs=results.difficulty_stderrs,
        metric_scores=results.metric_scores,  # Generic name for either metric
        metric_stderrs=results.metric_stderrs,  # Generic name for either metric
        take_hints_scores=results.take_hints_scores,
        samples=results.samples,
        output_path=config.results_dir,
    )


def main():
    """Main entry point with automatic restart on failure."""
    max_failure_duration = 3600  # 1 hour in seconds
    retry_delay = 10  # seconds between retries
    first_failure_time = None
    last_exception = None

    while True:
        try:
            run_once()
            break  # Success, exit loop
        except Exception as e:
            print("\n[ERROR] Run failed with exception:")
            traceback.print_exc()
            if first_failure_time is None:
                first_failure_time = time.time()
            else:
                elapsed = time.time() - first_failure_time
                if elapsed > max_failure_duration:
                    print(f"[FATAL] Run failed for over {max_failure_duration/60:.1f} minutes. Giving up.")
                    raise e
            print(f"[INFO] Restarting in {retry_delay} seconds...")
            time.sleep(retry_delay)
            last_exception = e


if __name__ == "__main__":
    main()
