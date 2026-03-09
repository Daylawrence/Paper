from factory_gui.planner.astar import AStarPlanner
from factory_gui.planner.greedy_best_first import GreedyBestFirstPlanner
from factory_gui.planner.registry import create_path_planner


def test_astar_returns_shortest_path_on_empty_grid():
    planner = AStarPlanner()
    path = planner.find_path(5, 5, set(), (0, 0), (2, 1))
    assert path[0] == (0, 0)
    assert path[-1] == (2, 1)
    assert len(path) == 4


def test_astar_routes_around_obstacles():
    planner = AStarPlanner()
    obstacles = {(1, 0), (1, 1), (1, 2)}
    path = planner.find_path(4, 4, obstacles, (0, 1), (3, 1))
    assert path[0] == (0, 1)
    assert path[-1] == (3, 1)
    assert (1, 1) not in path
    assert len(path) > 4


def test_astar_returns_empty_when_unreachable():
    planner = AStarPlanner()
    obstacles = {(1, 0), (1, 1), (1, 2)}
    path = planner.find_path(3, 3, obstacles, (0, 1), (2, 1))
    assert path == []


def test_greedy_best_first_finds_reachable_path():
    planner = GreedyBestFirstPlanner()
    obstacles = {(1, 0), (1, 1), (1, 2)}
    path = planner.find_path(4, 4, obstacles, (0, 1), (3, 1))
    assert path
    assert path[0] == (0, 1)
    assert path[-1] == (3, 1)


def test_path_planner_registry_resolves_all_supported_names():
    assert create_path_planner("astar").name == "astar"
    assert create_path_planner("greedy_best_first").name == "greedy_best_first"
