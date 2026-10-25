import core.maze as Mz
from core.algorithms.bfs import bfs


def main():
    maze = Mz.generate_maze(10, 10)
    print(maze)
    result = bfs(maze)

    print('Старт:', result['start'])
    print('Выход:', result['end'])
    print('Длина пути:', result['distance'])
    print('Количество исследованных клеток:', result['visited_count'])
    print('Маршрут:', result['path'])


if __name__ == '__main__':
    main()