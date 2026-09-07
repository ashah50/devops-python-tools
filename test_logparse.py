import pytest
from logparse import loud_levels, count_levels, find_ips, unique_levels, find_lines
from collections import Counter

@pytest.fixture
def sample_log(tmp_path):
    log = tmp_path / "sample.log"
    log.write_text(
        "2026-09-12 04:44:00 ERROR disk full 10.0.0.10\n"
        "2026-09-12 05:01:23 INFO ready 10.0.0.20\n"
        "2026-09-12 13:11:32 ERROR timeout 10.0.0.10\n"
        "2026-09-12 14:00:00 INFO connection reset 10.0.0.20\n"
        "2026-09-12 15:30:00 WARN resources low 10.0.0.10\n"
    )
    return log

@pytest.fixture
def make_log(tmp_path):
    def _make_log(contents, filename="test.log"):
        log = tmp_path / filename
        log.write_text(contents)
        return log
    return _make_log

def test_find_line(sample_log):
    assert find_lines(sample_log, "ERROR") == [
        "2026-09-12 04:44:00 ERROR disk full 10.0.0.10",
        "2026-09-12 13:11:32 ERROR timeout 10.0.0.10",
    ]

def test_count_levels(sample_log):
    assert count_levels(sample_log) == {"INFO": 2, "ERROR": 2, "WARN": 1}

def test_unique_levels(sample_log):
    assert unique_levels(sample_log) == {"INFO", "ERROR", "WARN"}

@pytest.mark.parametrize("counts, expected", [
    ({"INFO": 5, "ERROR": 1}, {"INFO": 5}),
    ({"A": 2, "B": 3, "C": 1}, {"A": 2, "B": 3}),
    ({"E": 2, "W": 2}, {"E": 2, "W": 2}),
    ({"X": 1}, {}),
    ({}, {}),
])
def test_loud_levels(counts, expected):
    assert loud_levels(counts) == expected

def test_find_ips(sample_log):
    assert find_ips(sample_log) == Counter({"10.0.0.10": 3, "10.0.0.20": 2})

@pytest.mark.parametrize("contents, expected", [
    ("10.0.0.1 \n10.0.0.1 \n10.0.0.2 \n",   Counter({"10.0.0.1": 2, "10.0.0.2": 1})),
    ("10.0.0.5 \n",                         Counter({"10.0.0.5": 1})),
    ("no ip addresses here\n",              Counter()),
])
def test_find_ips_cases(make_log, contents, expected):
    log = make_log(contents)
    assert find_ips(log) == expected