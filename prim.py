import argparse
import heapq
import json
import math
from pathlib import Path
from typing import TypeAlias


Vertex: TypeAlias = int | str | tuple[int, int, int]
Edge: TypeAlias = tuple[Vertex, Vertex]


class GraphDisconnectedError(ValueError):
    """Граф не является связным."""


def _vertex_name(value: str) -> int | str:
    try:
        return int(value)
    except ValueError:
        return value


def _prim_for_adjacency(graph: dict) -> tuple[float, list[Edge]]:
    adjacency: dict[int | str, dict[int | str, float]] = {}

    for raw_vertex, raw_neighbours in graph.items():
        vertex = _vertex_name(str(raw_vertex))
        if not isinstance(raw_neighbours, dict):
            raise ValueError("Каждой вершине должен соответствовать словарь соседей")
        adjacency.setdefault(vertex, {})

        for raw_neighbour, raw_weight in raw_neighbours.items():
            neighbour = _vertex_name(str(raw_neighbour))
            if isinstance(raw_weight, bool) or not isinstance(raw_weight, (int, float)):
                raise ValueError("Вес каждого ребра должен быть числом")
            weight = float(raw_weight)
            if not math.isfinite(weight):
                raise ValueError("Вес каждого ребра должен быть конечным числом")

            adjacency.setdefault(neighbour,  {})
            old_weight = adjacency[vertex].get(neighbour, math.inf)
            adjacency[vertex][neighbour] = min(old_weight, weight)
            old_weight = adjacency[neighbour].get(vertex, math.inf)
            adjacency[neighbour][vertex] = min(old_weight, weight)

    if not adjacency:
        return 0.0, []

    start = next(iter(adjacency))
    visited: set[int | str] = {start}
    queue: list[tuple[float, int, int | str, int | str]] = []
    order = 0
    for neighbour, weight in adjacency[start].items():
        heapq.heappush(queue, (weight, order, start, neighbour))
        order += 1

    total_weight = 0.0
    tree: list[Edge] = []

    while queue and len(visited) < len(adjacency):
        weight, _, parent, vertex = heapq.heappop(queue)
        if vertex in visited:
            continue

        visited.add(vertex)
        total_weight += weight
        tree.append((parent, vertex))

        for neighbour, next_weight in adjacency[vertex].items():
            if neighbour not in visited:
                heapq.heappush(queue, (next_weight, order, vertex, neighbour))
                order += 1

    if len(visited) != len(adjacency):
        raise GraphDisconnectedError("Граф не является связным")

    return total_weight, tree


def _cable_price(category_1: int, category_2: int) -> int:
    strictest_category = min(category_1, category_2)
    return 2 ** (3 - strictest_category)


def _prim_for_points(raw_points: list) -> tuple[float, list[Edge]]:
    points: list[tuple[int, int, int]] = []
    for raw_point in raw_points:
        if not isinstance(raw_point, (list, tuple)) or len(raw_point) != 3:
            raise ValueError("Каждая вершина должна иметь вид [x, y, category]")
        x, y, category = raw_point
        if (isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, int) or not isinstance(y, int)):
            raise ValueError("Координаты вершины должны быть целыми числами")
        if category not in (1, 2, 3):
            raise ValueError("Категория вершины должна быть равна 1, 2 или 3")
        points.append((x, y, category))

    count = len(points)
    if count == 0:
        return 0.0, []

    in_tree = [False] * count
    min_weight = [math.inf] * count
    parent = [-1] * count
    min_weight[0] = 0.0
    total_weight = 0.0
    tree_indices: list[tuple[int, int]] = []

    for _ in range(count):
        vertex = -1
        for candidate in range(count):
            if not in_tree[candidate] and (vertex == -1 or min_weight[candidate] < min_weight[vertex]):
                vertex = candidate

        if vertex == -1 or math.isinf(min_weight[vertex]):
            raise GraphDisconnectedError("Граф не является связным")

        in_tree[vertex] = True
        total_weight += min_weight[vertex]
        if parent[vertex] != -1:
            tree_indices.append((parent[vertex], vertex))

        x_1, y_1, category_1 = points[vertex]
        for neighbour in range(count):
            if in_tree[neighbour]:
                continue
            x_2, y_2, category_2 = points[neighbour]
            distance = math.hypot(x_1 - x_2, y_1 - y_2)
            weight = distance * _cable_price(category_1, category_2)
            if weight < min_weight[neighbour]:
                min_weight[neighbour] = weight
                parent[neighbour] = vertex

    tree: list[Edge] = [(points[first], points[second]) for first, second in tree_indices]
    return total_weight, tree


def prim_mst(graph: dict | list) -> tuple[float, list[Edge]]:
    if isinstance(graph, dict):
        return _prim_for_adjacency(graph)
    if isinstance(graph, list):
        return _prim_for_points(graph)
    raise ValueError("JSON должен содержать словарь или список")


def _format_weight(weight: float) -> str:
    if weight.is_integer():
        return str(int(weight))
    return f"{weight:.6f}".rstrip("0").rstrip(".")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Поиск минимального остовного дерева алгоритмом Прима")
    parser.add_argument("input", type=Path, help="Путь к входному JSON-файлу")
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    try:
        with args.input.open(encoding="utf-8") as input_file:
            graph = json.load(input_file)
        total_weight, edges = prim_mst(graph)
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"Не удалось прочитать JSON: {error}")
    except (ValueError, GraphDisconnectedError) as error:
        parser.error(str(error))

    print(f"Вес минимального остовного дерева: {_format_weight(total_weight)}")
    for first, second in edges:
        print(f"({first}, {second})")


if __name__ == "__main__":
    main()
