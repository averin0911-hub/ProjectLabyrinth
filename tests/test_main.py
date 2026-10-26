import contextlib
import copy
import io
import unittest
import weakref
from unittest.mock import patch

import main
from core.algorithms.bfs import bfs
from core.algorithms.dijkstra import dijkstra
from core.maze import Maze


class ComparisonTests(unittest.TestCase):
    def test_equal_distances_can_have_different_visited_counts(self):
        maze = Maze([[0] * 7 for _ in range(7)], start=(3, 3), end=(3, 5))
        original = copy.deepcopy(maze.grid)
        results = [bfs(maze), dijkstra(maze)]

        self.assertEqual([result["distance"] for result in results], [2, 2])
        self.assertEqual([result["visited_count"] for result in results], [13, 10])
        for result in results:
            self.assertEqual(len(set(result["visited_order"])), result["visited_count"])
            self.assertEqual(result["path"][0], maze.start)
            self.assertEqual(result["path"][-1], maze.end)
            for current, neighbor in zip(result["path"], result["path"][1:]):
                self.assertIn(neighbor, maze.neighbors(*current))
        self.assertEqual(maze.grid, original)

    def test_comparison_runs_each_algorithm_once_and_releases_results(self):
        class Result(dict):
            pass

        maze = Maze([[2, 0]], end=(0, 1))
        calls = []
        references = []
        times = iter([12.0, 33.0])

        def measure(field, algorithm):
            self.assertIs(field, maze)
            self.assertTrue(all(reference() is None for reference in references))
            calls.append(algorithm)
            result = Result(distance=1, visited_count=2)
            references.append(weakref.ref(result))
            return result, next(times)

        output = io.StringIO()
        with (
            patch("main.measure_algorithm", side_effect=measure),
            patch("main.show_maze", side_effect=AssertionError("Карты не входят в сравнение")),
            contextlib.redirect_stdout(output),
        ):
            main.compare_algorithms(maze)

        self.assertEqual(calls, [bfs, dijkstra])
        self.assertTrue(all(reference() is None for reference in references))
        rows = [line.split() for line in output.getvalue().splitlines()]
        self.assertIn(["BFS", "1", "2", "12.000"], rows)
        self.assertIn(["Дейкстра", "1", "2", "33.000"], rows)
        self.assertIn("Всего клеток: 2; проходимых: 2", output.getvalue())

    def test_timer_excludes_rendering(self):
        maze = Maze([[2, 0]], end=(0, 1))
        with (
            patch("main.perf_counter", side_effect=[10.0, 10.125]) as timer,
            patch("main.show_maze") as render,
            contextlib.redirect_stdout(io.StringIO()),
        ):
            render.side_effect = lambda *args: self.assertEqual(timer.call_count, 2)
            result, elapsed_ms = main.run_algorithm(maze, "BFS", bfs)
        self.assertEqual(result["distance"], 1)
        self.assertEqual(elapsed_ms, 125.0)
        render.assert_called_once()

    def test_no_path_returns_to_menu(self):
        maze = Maze([[2, 1, 3]], end=(0, 2))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            main.compare_algorithms(maze)
        self.assertIn("Путь до выхода не существует", output.getvalue())

    def test_size_validation_matches_configured_limit(self):
        output = io.StringIO()
        with (
            patch("main.MAX_SIZE", 2000),
            patch("builtins.input", side_effect=["bad", "4", "2001", "2000"]),
            contextlib.redirect_stdout(output),
        ):
            self.assertEqual(main.read_size("Ширина"), 2000)
        self.assertIn("от 5 до 2000", output.getvalue())
        self.assertNotIn("до 500", output.getvalue())


if __name__ == "__main__":
    unittest.main()
