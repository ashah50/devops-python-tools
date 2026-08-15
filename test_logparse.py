import pytest                                                               
from logparse import loud_levels, count_levels                              
                                                                            
                                                                            
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
