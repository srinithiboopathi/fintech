import math
from typing import List, Dict, Any, Tuple

class CorrelationMatrix:
    @staticmethod
    def pearson_correlation(x: List[float], y: List[float]) -> float:
        n = min(len(x), len(y))
        if n < 2:
            return 0.0

        x = x[:n]
        y = y[:n]
        mean_x = sum(x) / n
        mean_y = sum(y) / n

        num = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        den_x = math.sqrt(sum((x[i] - mean_x) ** 2 for i in range(n)))
        den_y = math.sqrt(sum((y[i] - mean_y) ** 2 for i in range(n)))

        if den_x == 0 or den_y == 0:
            return 0.0
        return round(num / (den_x * den_y), 4)

    @staticmethod
    def rank_data(series: List[float]) -> List[float]:
        """
        Calculates rank of elements for Spearman Rank Correlation.
        """
        indexed = sorted(enumerate(series), key=lambda item: item[1])
        ranks = [0.0] * len(series)
        i = 0
        while i < len(indexed):
            j = i
            while j < len(indexed) - 1 and indexed[j + 1][1] == indexed[j][1]:
                j += 1
            rank = (i + j + 2) / 2.0
            for k in range(i, j + 1):
                ranks[indexed[k][0]] = rank
            i = j + 1
        return ranks

    @staticmethod
    def spearman_correlation(x: List[float], y: List[float]) -> float:
        n = min(len(x), len(y))
        if n < 2:
            return 0.0
        rx = CorrelationMatrix.rank_data(x[:n])
        ry = CorrelationMatrix.rank_data(y[:n])
        return CorrelationMatrix.pearson_correlation(rx, ry)

    @staticmethod
    def calculate_matrix(data_dict: Dict[str, List[float]], symbols: List[str], method: str = "pearson") -> List[List[float]]:
        matrix = []
        for s1 in symbols:
            row = []
            x = data_dict.get(s1, [])
            for s2 in symbols:
                if s1 == s2:
                    row.append(1.0)
                else:
                    y = data_dict.get(s2, [])
                    if method.lower() == "spearman":
                        corr = CorrelationMatrix.spearman_correlation(x, y)
                    else:
                        corr = CorrelationMatrix.pearson_correlation(x, y)
                    row.append(corr)
            matrix.append(row)
        return matrix
