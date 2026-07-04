from src.models import DecisionStep


class DecisionLog:
    """Helper to build transparent agent decision trails."""

    def __init__(self) -> None:
        self.steps: list[DecisionStep] = []
        self._counter = 0

    def add(
        self,
        rule: str,
        input_summary: str,
        outcome: str,
        **metadata: object,
    ) -> "DecisionLog":
        self._counter += 1
        clean_meta = {k: v for k, v in metadata.items() if v is not None}
        self.steps.append(
            DecisionStep(
                step=self._counter,
                rule=rule,
                input_summary=input_summary,
                outcome=outcome,
                metadata=clean_meta,
            )
        )
        return self
