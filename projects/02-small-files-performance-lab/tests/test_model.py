import math
from pathlib import Path
import pytest
from small_files.model import Config, break_even, file_stats, summarize

@pytest.mark.parametrize('overrides',[{'rows':0},{'seed':1.2},{'iterations':2},{'fragmented_files':4},{'compacted_files':3},{'compute_hour_cost':float('nan')},{'warmups':0},{'cores':True},{'partitioned':'yes'},{'compaction_seconds':-1},{'compute_hour_cost':None}])
def test_invalid_config(overrides):
    with pytest.raises(ValueError):
        Config(**overrides).validate()

def test_valid_config():
    Config().validate()
    Config(partitioned=False,compacted_files=3).validate()

def test_statistics():
    s=summarize([1,2,3,4,5])
    assert s['median_seconds']==3 and s['iqr_seconds']==2

@pytest.mark.parametrize('samples',[[1],[1,0,2],[1,math.nan,2],[1,math.inf,2]])
def test_invalid_samples(samples):
    with pytest.raises(ValueError):
        summarize(samples)

def test_files(tmp_path):
    with pytest.raises(FileNotFoundError):
        file_stats(tmp_path)
    (tmp_path/'part.parquet').write_bytes(b'abc')
    (tmp_path/'_SUCCESS').touch()
    assert file_stats(tmp_path)['parquet_bytes']==3
    assert file_stats(tmp_path)['files']==1

def test_break_even():
    assert break_even(10,3,1,2)['break_even_reads']==5
    assert break_even(10,3,1,2)['compaction_compute_cost']==pytest.approx(20/3600)
    assert break_even(10,3,1,0)['cost_break_even_reads'] is None
    assert break_even(10,1,3,2)['break_even_reads'] is None
    assert break_even(0,3,1,2)['break_even_reads']==0

@pytest.mark.parametrize('value',[-1,math.nan,math.inf])
def test_bad_economics(value):
    with pytest.raises(ValueError):
        break_even(value,3,1,2)
