import pytest
from app.correlation.matrix import CorrelationMatrix
from app.correlation.rolling import RollingCorrelation

def test_pearson_correlation_perfect():
    x = [0.01, 0.02, 0.03, 0.04, 0.05]
    y = [0.02, 0.04, 0.06, 0.08, 0.10]
    corr = CorrelationMatrix.pearson_correlation(x, y)
    assert round(corr, 4) == 1.0

def test_pearson_correlation_inverse():
    x = [0.01, 0.02, 0.03, 0.04, 0.05]
    y = [-0.01, -0.02, -0.03, -0.04, -0.05]
    corr = CorrelationMatrix.pearson_correlation(x, y)
    assert round(corr, 4) == -1.0

def test_spearman_correlation():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [10.0, 20.0, 30.0, 40.0, 50.0]
    corr = CorrelationMatrix.spearman_correlation(x, y)
    assert round(corr, 4) == 1.0

def test_correlation_matrix_generation():
    data = {
        "A": [0.01, -0.02, 0.03, -0.01, 0.02],
        "B": [0.02, -0.04, 0.06, -0.02, 0.04],
        "C": [-0.01, 0.02, -0.03, 0.01, -0.02]
    }
    symbols = ["A", "B", "C"]
    mat = CorrelationMatrix.calculate_matrix(data, symbols, method="pearson")
    assert len(mat) == 3
    assert len(mat[0]) == 3
    assert mat[0][0] == 1.0
    assert mat[1][1] == 1.0
    assert mat[2][2] == 1.0
    assert round(mat[0][1], 2) == 1.0
    assert round(mat[0][2], 2) == -1.0

def test_rolling_correlation():
    dates = [f"2023-01-{i+1:02d}" for i in range(20)]
    rets_a = [0.01 * (1 if i % 2 == 0 else -1) for i in range(20)]
    rets_b = [0.01 * (1 if i % 2 == 0 else -1) for i in range(20)]
    rolling = RollingCorrelation.calculate_rolling(dates, rets_a, rets_b, window=5)
    assert len(rolling) == 20
    assert rolling[0]["correlation"] is None
    assert rolling[3]["correlation"] is None
    assert rolling[4]["correlation"] is not None
    assert round(rolling[4]["correlation"], 2) == 1.0
