from random import Random

from mazegen.grid import Grid, Position
from mazegen.strategies.base import GenerationStrategy


class FakeStrategy:
    """Minimal strategy used to verify the GenerationStrategy contract."""

    def generate(
        self,
        grid: Grid,
        rng: Random,
        reserved: set[Position],
    ) -> Grid:
        _ = rng.random()
        assert isinstance(reserved, set)
        return grid


def test_fake_strategy_satisfies_generation_strategy_contract() -> None:
    strategy: GenerationStrategy = FakeStrategy()
    grid = Grid(2, 2)
    rng = Random(42)
    reserved = {Position(0, 0)}

    assert strategy.generate(grid, rng, reserved) is grid
