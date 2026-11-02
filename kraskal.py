import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias


Vertex: TypeAlias = int | str | tuple[int, int, int]
TreeEdge: TypeAlias = tuple[Vertex, Vertex]


@dataclass
class Edge:
    from_value: Vertex
    to_value: Vertex
    weight: float


class DisjoinSet:
    def __init__(self, size: int):
        self.parent = list(range(size))
        self.component_size = [1] * size
        self.components = size

    def find(self, value: int) -> int:
        root = value
        while self.parent[root] != root:
            root = self.parent[root]

        while self.parent[value] != value:
            parent = self.parent[value]
            self.parent[value] = root
            value = parent
        return root

    def union(self, first: int, second: int) -> bool:
        first_root = self.find(first)
        second_root = self.find(second)
        if first_root == second_root:
            return False

        if self.component_size[first_root] < self.component_size[second_root]:
            first_root, second_root = second_root, first_root

        self.parent[second_root] = first_root
        self.component_size[first_root] += self.component_size[second_root]
        self.components -= 1
        return True


def _vertex_name(value: object) -> int | str:
    text = str(value)
    try:
        return int(text)
    except ValueError:
        return text


def _validate_weight(raw_weight: object) -> float:
    if isinstance(raw_weight, bool) or not isinstance(raw_weight, (int, float)):
        raise ValueError("Вес каждого ребра должен быть числом")
    weight = float(raw_weight)
    if not math.isfinite(weight):
        raise ValueError("Вес каждого ребра должен быть конечным числом")
    return weight


def _edges_from_adjacency(graph: dict) -> tuple[list[Vertex], list[tuple[float, int, int]]]:
    vertices: list[Vertex] = []
    vertex_index: dict[Vertex, int] = {}

    def add_vertex(vertex: Vertex) -> int:
        if vertex not in vertex_index:
            vertex_index[vertex] = len(vertices)
            vertices.append(vertex)
        return vertex_index[vertex]

    for raw_vertex, raw_neighbours in graph.items():
        if not isinstance(raw_neighbours, dict):
            raise ValueError("Каждой вершине должен соответствовать словарь соседей")
        add_vertex(_vertex_name(raw_vertex))
        for raw_neighbour in raw_neighbours:
            add_vertex(_vertex_name(raw_neighbour))

    edge_weights: dict[tuple[int, int], float] = {}
    for raw_vertex, raw_neighbours in graph.items():
        first = vertex_index[_vertex_name(raw_vertex)]
        for raw_neighbour, raw_weight in raw_neighbours.items():
            second = vertex_index[_vertex_name(raw_neighbour)]
            if first == second:
                continue
            pair = (first, second) if first < second else (second, first)
            weight = _validate_weight(raw_weight)
            edge_weights[pair] = min(edge_weights.get(pair, math.inf), weight)

    edges = [(weight, first, second) for (first, second), weight in edge_weights.items()]
    return vertices, edges


def _validate_points(raw_points: list) -> list[tuple[int, int, int]]:
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
    return points


def _cable_price(category_1: int, category_2: int) -> int:
    strictest_category = min(category_1, category_2)
    return 2 ** (3 - strictest_category)


def _edges_from_points(raw_points: list) -> tuple[list[Vertex], list[tuple[float, int, int]]]:
    points = _validate_points(raw_points)
    edges: list[tuple[float, int, int]] = []

    for first in range(len(points)):
        x_1, y_1, category_1 = points[first]
        for second in range(first + 1, len(points)):
            x_2, y_2, category_2 = points[second]
            distance = math.hypot(x_1 - x_2, y_1 - y_2)
            weight = distance * _cable_price(category_1, category_2)
            edges.append((weight, first, second))

    return list(points), edges


def _kruskal(vertices: list[Vertex], edges: list[tuple[float, int, int]]) -> tuple[float, list[TreeEdge], int]:
    disjoint_set = DisjoinSet(len(vertices))
    total_weight = 0.0
    forest: list[TreeEdge] = []

    edges.sort(key=lambda edge: (edge[0], edge[1], edge[2]))
    for weight, first, second in edges:
        if not disjoint_set.union(first, second):
            continue

        total_weight += weight
        forest.append((vertices[first], vertices[second]))
        if disjoint_set.components == 1:
            break

    return total_weight, forest, disjoint_set.components


def kruskal_forest(graph: dict | list) -> tuple[float, list[TreeEdge], int]:
    if isinstance(graph, dict):
        vertices, edges = _edges_from_adjacency(graph)
    elif isinstance(graph, list):
        vertices, edges = _edges_from_points(graph)
    else:
        raise ValueError("JSON должен содержать словарь или список")
    return _kruskal(vertices, edges)


def kruskal_mst(graph: dict | list) -> tuple[float, list[TreeEdge]]:
    total_weight, edges, _ = kruskal_forest(graph)
    return total_weight, edges


def _format_weight(weight: float) -> str:
    if weight.is_integer():
        return str(int(weight))
    return f"{weight:.6f}".rstrip("0").rstrip(".")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Поиск минимального остовного дерева алгоритмом Краскала")
    parser.add_argument("input", type=Path, help="Путь к входному JSON-файлу")
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    try:
        with args.input.open(encoding="utf-8") as input_file:
            graph = json.load(input_file)
        total_weight, edges, components = kruskal_forest(graph)
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"Не удалось прочитать JSON: {error}")
    except ValueError as error:
        parser.error(str(error))

    result_name = "дерева" if components <= 1 else "леса"
    print(f"Вес минимального остовного {result_name}: {_format_weight(total_weight)}")
    for first, second in edges:
        print(f"({first}, {second})")


if __name__ == "__main__":
    main()
