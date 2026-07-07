import random


class CanaryRouter:
    def __init__(self, canary_percentage: int = 10, random_seed: int | None = None) -> None:
        if not 0 <= canary_percentage <= 100:
            raise ValueError("canary_percentage must be between 0 and 100")
        self.canary_percentage = canary_percentage
        self._random = random.Random(random_seed)

    def route(self) -> str:
        return "v2" if self._random.random() < self.canary_percentage / 100 else "v1"

