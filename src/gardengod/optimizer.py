"""Garden optimization engine using companion planting rules."""

from gardengod.models import Plant, Garden, GridCell


def get_adjacent_cells(
    grid: list[GridCell], x: int, y: int, width: int, height: int
) -> list[GridCell]:
    """Get all adjacent cells (including diagonals) for a given position."""
    adjacent = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                for cell in grid:
                    if cell.x == nx and cell.y == ny:
                        adjacent.append(cell)
                        break
    return adjacent


def calculate_companion_score(
    plant: Plant,
    adjacent_plants: list[Plant],
) -> int:
    """
    Calculate a score for placing a plant based on its neighbors.

    +1 for each companion neighbor
    -2 for each antagonist neighbor (stronger penalty)
    """
    score = 0
    for neighbor in adjacent_plants:
        if neighbor.id in plant.companions:
            score += 1
        if neighbor.id in plant.antagonists:
            score -= 2
    return score


def find_best_cell_for_plant(
    garden: Garden,
    plant: Plant,
    plants_db: dict[str, Plant],
) -> GridCell | None:
    """
    Find the best empty cell to place a plant, maximizing companion score.

    Returns None if no empty cells are available.
    """
    best_cell: GridCell | None = None
    best_score = float("-inf")

    for cell in garden.grid:
        if cell.plant_id is not None:
            continue  # Cell is occupied

        adjacent_cells = get_adjacent_cells(
            garden.grid, cell.x, cell.y, garden.width, garden.height
        )
        adjacent_plants = [
            plants_db[c.plant_id] for c in adjacent_cells if c.plant_id in plants_db
        ]

        score = calculate_companion_score(plant, adjacent_plants)

        if score > best_score:
            best_score = score
            best_cell = cell

    return best_cell


def optimize_garden(
    garden: Garden,
    plants_to_place: list[str],
    plants_db: dict[str, Plant],
) -> Garden:
    """
    Place plants in the garden optimizing for companion planting.

    Args:
        garden: The garden with an initialized empty grid.
        plants_to_place: List of plant IDs to place (can have duplicates).
        plants_db: Dictionary mapping plant IDs to Plant objects.

    Returns:
        The garden with plants placed optimally.
    """
    for plant_id in plants_to_place:
        if plant_id not in plants_db:
            raise ValueError(f"Unknown plant ID: {plant_id}")

        plant = plants_db[plant_id]
        best_cell = find_best_cell_for_plant(garden, plant, plants_db)

        if best_cell is None:
            raise ValueError("Garden is full, cannot place more plants")

        best_cell.plant_id = plant_id

    return garden


def calculate_garden_score(garden: Garden, plants_db: dict[str, Plant]) -> int:
    """Calculate the total companion score for the entire garden."""
    total_score = 0

    for cell in garden.grid:
        if cell.plant_id is None:
            continue

        plant = plants_db.get(cell.plant_id)
        if plant is None:
            continue

        adjacent_cells = get_adjacent_cells(
            garden.grid, cell.x, cell.y, garden.width, garden.height
        )
        adjacent_plants = [
            plants_db[c.plant_id] for c in adjacent_cells if c.plant_id in plants_db
        ]

        total_score += calculate_companion_score(plant, adjacent_plants)

    # Divide by 2 because each pair is counted twice
    return total_score // 2
