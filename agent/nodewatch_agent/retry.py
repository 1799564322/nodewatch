import random


class ExponentialBackoff:
    def __init__(self, maximum: int, random_source: random.Random | None = None) -> None:
        self.maximum = maximum
        self.attempt = 0
        self.random = random_source or random.Random()

    def next_delay(self) -> float:
        ceiling = min(self.maximum, 2**self.attempt)
        self.attempt += 1
        return self.random.uniform(0, ceiling)

    def reset(self) -> None:
        self.attempt = 0
