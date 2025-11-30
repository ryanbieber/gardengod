import pytest
from gardengod.models import Plant, Garden
from gardengod.optimizer import (
    get_adjacent_cells,
    calculate_companion_score,
    optimize_garden,
    calculate_garden_score,
)


@pytest.fixture
def sample_plants() -> dict[str, Plant]:
    return {
        "tomato": Plant(
            id="tomato",
            name="Tomato",
            spacing_per_sqft=1,
            companions=["basil", "carrot"],
            antagonists=["cabbage"],
        ),
        "basil": Plant(
            id="basil",
            name="Basil",
            spacing_per_sqft=4,
            companions=["tomato"],
            antagonists=[],
        ),
        "cabbage": Plant(
            id="cabbage",
            name="Cabbage",
            spacing_per_sqft=1,
            companions=[],
            antagonists=["tomato"],
        ),
    }


@pytest.fixture
def empty_3x3_garden() -> Garden:
    garden = Garden(width=3, height=3)
    garden.initialize_grid()
    return garden


def test_get_adjacent_cells_corner(empty_3x3_garden: Garden) -> None:
    """Test that corner cells have exactly 3 adjacent cells."""
    adjacent = get_adjacent_cells(empty_3x3_garden.grid, 0, 0, 3, 3)
    assert len(adjacent) == 3
    positions = [(c.x, c.y) for c in adjacent]
    assert (1, 0) in positions
    assert (0, 1) in positions
    assert (1, 1) in positions


def test_get_adjacent_cells_center(empty_3x3_garden: Garden) -> None:
    """Test that center cell has 8 adjacent cells."""
    adjacent = get_adjacent_cells(empty_3x3_garden.grid, 1, 1, 3, 3)
    assert len(adjacent) == 8


def test_calculate_companion_score_positive(sample_plants: dict[str, Plant]) -> None:
    """Test that companions give positive score."""
    tomato = sample_plants["tomato"]
    neighbors = [sample_plants["basil"]]
    score = calculate_companion_score(tomato, neighbors)
    assert score == 1


def test_calculate_companion_score_negative(sample_plants: dict[str, Plant]) -> None:
    """Test that antagonists give negative score."""
    tomato = sample_plants["tomato"]
    neighbors = [sample_plants["cabbage"]]
    score = calculate_companion_score(tomato, neighbors)
    assert score == -2


def test_calculate_companion_score_mixed(sample_plants: dict[str, Plant]) -> None:
    """Test mixed companions and antagonists."""
    tomato = sample_plants["tomato"]
    neighbors = [sample_plants["basil"], sample_plants["cabbage"]]
    score = calculate_companion_score(tomato, neighbors)
    assert score == -1  # +1 for basil, -2 for cabbage


def test_optimize_garden_places_plants(
    empty_3x3_garden: Garden, sample_plants: dict[str, Plant]
) -> None:
    """Test that optimization places all requested plants."""
    plants_to_place = ["tomato", "basil", "tomato"]
    result = optimize_garden(empty_3x3_garden, plants_to_place, sample_plants)

    placed_plants = [c.plant_id for c in result.grid if c.plant_id is not None]
    assert len(placed_plants) == 3
    assert placed_plants.count("tomato") == 2
    assert placed_plants.count("basil") == 1


def test_optimize_garden_fails_when_full(
    sample_plants: dict[str, Plant],
) -> None:
    """Test that optimization raises when garden is full."""
    garden = Garden(width=1, height=1)
    garden.initialize_grid()

    with pytest.raises(ValueError, match="Garden is full"):
        optimize_garden(garden, ["tomato", "basil"], sample_plants)


def test_calculate_garden_score(
    empty_3x3_garden: Garden, sample_plants: dict[str, Plant]
) -> None:
    """Test garden score calculation."""
    # Place tomato at (0,0) and basil at (1,0) - they are companions
    empty_3x3_garden.grid[0].plant_id = "tomato"
    empty_3x3_garden.grid[1].plant_id = "basil"

    score = calculate_garden_score(empty_3x3_garden, sample_plants)
    # tomato gets +1 for basil neighbor, basil gets +1 for tomato neighbor
    # Total = 2, divided by 2 = 1
    assert score == 1
