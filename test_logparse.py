import pytest                                                               
from logparse import loud_levels, count_levels, find_ips
from collections import Counter
                                                                            
                                                                            
@pytest.mark.parametrize("counts, expected", [                              
    ({"INFO": 5, "ERROR": 1}, {"INFO": 5}),                                 
    ({"A": 2, "B": 3, "C": 1}, {"A": 2, "B": 3}),                           
    ({"E": 2, "W": 2}, {"E": 2, "W": 2}),
    ({"X": 1}, {}),
    ({}, {}),                         
])                                    
def test_loud_levels(counts, expected):
    assert loud_levels(counts) == expected
                                    

def test_count_levels(tmp_path):
    log = tmp_path / "sample.log"          # a path inside the temp dir
    log.write_text(                        # write a KNOWN log file
        "2026-01-01 10:00:00 INFO started\n"
        "2026-01-01 10:00:01 ERROR disk full\n"
        "2026-01-01 10:00:02 INFO ready\n"
        "2026-01-01 10:00:03 ERROR timeout\n"
    )
    assert count_levels(log) == {"INFO": 2, "ERROR": 2}

def test_find_ips(tmp_path):
    log = tmp_path / "sampleips.log"
    log.write_text(
        "10.0.0.10 \n"
        "10.0.0.20 \n"
        "10.0.0.10 \n"
        "10.0.0.20 \n"
        "10.0.0.10 \n"
    )
    assert find_ips(log) == Counter({"10.0.0.10": 99, "10.0.0.20": 2})

@pytest.mark.parametrize("contents, expected", [
    ("10.0.0.1 \n10.0.0.1 \n10.0.0.2 \n",   Counter({"10.0.0.1": 2, "10.0.0.2": 1})),
    ("10.0.0.5 \n",                         Counter({"10.0.0.5": 1})),
    ("no ip addresses here\n",              Counter()),
  ])
def test_find_ips_cases(tmp_path, contents, expected):
    log = tmp_path / "t.log"
    log.write_text(contents)
    assert find_ips(log) == expected
