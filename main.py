import core.maze
import core.algorithms.dijkstra as dijkstra

maze = core.maze.generate_maze(15, 15, 1)
print(maze)
print(dijkstra.dijkstra(maze)["visited_order"])