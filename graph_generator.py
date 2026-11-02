import argparse
import json

from generators import lch


class GraphGenerator:
    def __init__(self, m: int, a: int, c: int, x0: int):
        self.m = m
        self.a = a
        self.c = c
        self.xn = x0
        self.__generator = lch(x0, a, c, m)

    def __next_number(self) -> int:
        self.xn = next(self.__generator)
        return self.xn

    def __rand_p(self) -> float:
        x = self.__next_number()
        return x / self.m 

    def __rand_range(self, left: int, right: int) -> int:
        x = self.__next_number()
        return left + x % (right - left + 1)

    def random_erg_graph(self, n: int, p: float, min_w: int, max_w: int) -> dict[int, dict[int, int]]:
        graph = {node: {} for node in range(n)}
        for i in range(n):
            for j in range(i + 1, n):
                if self.__rand_p() < p:
                    weight = self.__rand_range(min_w, max_w)
                    graph[i][j] = weight
                    graph[j][i] = weight
        return graph
    
    def random_planar_graph(self, n: int, width: int, height: int, p_first: float, p_second: float) -> list[tuple[int, int, int]]:
        points = {}
        for _ in range(n):
            x = self.__rand_range(0, width)
            y = self.__rand_range(0, height)
            probability = self.__rand_p()
            if probability < p_first:
                category = 1
            elif probability < p_first + p_second:
                category = 2
            else:
                category = 3

            position = (x, y)
            points[position] = min(category, points.get(position, 3))

        return [(x, y, category) for (x, y), category in points.items()]


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Генерация случайных графов")
    subparsers = parser.add_subparsers(dest="graph", required=True)

    erg = subparsers.add_parser("erg", help="Граф Эрдёша — Реньи — Гилберта")
    planar = subparsers.add_parser("planar", help="Точки на плоскости с категориями", add_help=False)
    planar.add_argument("--help", action="help", help="Показать справку")

    for graph_parser in (erg, planar):
        graph_parser.add_argument("--number", "-n", type=int, required=True, help="Число вершин" )
        graph_parser.add_argument("--output", "-o", required=True, help="Путь к выходному JSON-файлу")

    erg.add_argument("--probability", "-p", type=float, required=True, help="Вероятность ребра")
    erg.add_argument("--min-weight", "-minw", type=int, required=True, help="Минимальный вес")
    erg.add_argument("--max-weight", "-maxw", type=int, required=True, help="Максимальный вес")
    planar.add_argument("--width", "-w", type=int, required=True, help="Максимальная x-координата")
    planar.add_argument("--height", "-h", type=int, required=True, help="Максимальная y-координата")
    planar.add_argument("--p-first", "-p1", type=float, required=True, help="Вероятность категории 1")
    planar.add_argument("--p-second", "-p2", type=float, required=True, help="Вероятность категории 2")
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    generator = GraphGenerator(m=2**32, a=134775813, c=1, x0=1)
    try:
        if args.graph == "erg":
            graph = generator.random_erg_graph(
                args.number, args.probability, args.min_weight, args.max_weight
            )
        else:
            graph = generator.random_planar_graph(
                args.number, args.width, args.height, args.p_first, args.p_second
            )
    except ValueError as error:
        parser.error(str(error))

    try:
        with open(args.output, "w", encoding="utf-8") as output:
            json.dump(graph, output, ensure_ascii=False, indent=4)
            output.write("\n")
    except OSError as error:
        parser.error(f"Не удалось записать JSON: {error}")


if __name__ == "__main__":
    main()


#python3 graph_generator.py erg -n 10 -p 0.5 -minw 1 -maxw 10 -o output/erg.json
#python3 graph_generator.py planar -n 20 -w 100 -h 100 -p1 0.3 -p2 0.4 -o output/planar.json
