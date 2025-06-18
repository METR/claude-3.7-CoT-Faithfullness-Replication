from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
from typing import Optional, Literal

from clue_difficulty import TestingScheme


MetricType = Literal["auditability", "faithfulness"]


@dataclass
class EvalConfig:
    model: str
    reasoning_difficulty_model: Optional[str]
    base_model: str
    display: str
    testing_scheme: TestingScheme
    redteam: bool
    temperature: float
    max_connections: int
    filtered_csv: Optional[str]
    question_prompt: str
    judge_prompt: str
    metric_type: MetricType
    output_dir: Path

    @property
    def model_short_name(self) -> str:
        """Get shortened model name for file naming."""
        return ''.join([j[0] for j in self.model.replace('/', '-').split('-')])

    @property
    def experiment_id(self) -> str:
        """Generate unique experiment identifier."""
        metric_prefix = "A" if self.metric_type == "auditability" else "F"
        return (
            f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-"
            f"{self.model_short_name}-"
            f"{metric_prefix}_"
            f"Q_{Path(self.question_prompt).stem}-"
            f"J_{Path(self.judge_prompt).stem}"
        )

    @property
    def log_dir(self) -> Path:
        """Get log directory for this run."""
        return self.output_dir / "logs" / self.experiment_id

    @property
    def results_dir(self) -> Path:
        """Get results directory for this run."""
        metric_dir = "auditability" if self.metric_type == "auditability" else "faithfulness"
        return self.output_dir / "results" / metric_dir / f"{self.experiment_id}.json"

    def __post_init__(self):
        """Validate and process config after initialization."""
        # Convert string paths to Path objects
        self.output_dir = Path(self.output_dir)
        
        # Create output directories
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.parent.mkdir(parents=True, exist_ok=True)

        # Set reasoning model to main model if not specified
        if self.reasoning_difficulty_model is None:
            self.reasoning_difficulty_model = self.model

        # Validate testing scheme
        if isinstance(self.testing_scheme, str):
            self.testing_scheme = TestingScheme(self.testing_scheme.lower())

        # Validate metric type
        if not isinstance(self.metric_type, str) or self.metric_type not in ("auditability", "faithfulness"):
            raise ValueError("metric_type must be either 'auditability' or 'faithfulness'") 