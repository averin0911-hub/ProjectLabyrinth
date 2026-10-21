import core.maze
import core.algorithms.dijkstra as dijkstra

maze = core.maze.generate_maze(19, 19)
print(maze)
# print(dijkstra.dijkstra(maze)["visited_order"])