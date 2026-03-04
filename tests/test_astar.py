from factory_gui.planner.astar import AStarPlanner


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
