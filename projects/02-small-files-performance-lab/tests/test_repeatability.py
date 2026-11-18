import pytest
from small_files.repeatability import normalize_plan, variability

def test_plan_normalization():
    a='Filter (customer_id#123L < 1000) [plan_id=4] Location [file:/a/fragmented]'
    b='Filter (customer_id#456L < 1000) [plan_id=9] Location [file:/b/compacted]'
    assert normalize_plan(a)==normalize_plan(b)
    assert normalize_plan(a)!=normalize_plan(b.replace('1000','2000'))

def test_variability():
    s=variability([1,2,3,4,5])
    assert s['median_seconds']==3
    assert s['sample_stdev']==pytest.approx(1.58113883)
    assert s['cv_percent']==pytest.approx(52.7046277)

@pytest.mark.parametrize('values',[[1],[1,2],[1,0,2],[1,float('nan'),2]])
def test_invalid_variability(values):
    with pytest.raises(ValueError):
        variability(values)

def test_duplicate_run_ids_are_not_independent(tmp_path):
    import json
    from small_files.repeatability import analyze
    paths=[]
    for i in range(3):
        p=tmp_path/str(i)
        p.mkdir()
        (p/'report.json').write_text(json.dumps({'run_id':'same-application'}))
        paths.append(p)
    with pytest.raises(ValueError,match='distinct independent'):
        analyze(paths,tmp_path/'summary')

def test_restore_truncated_plan_display():
    from small_files.repeatability import complete_plan
    a='FileScan DataFilters: [status#12 = con..., Format: Parquet'
    b='FileScan DataFilters: [status#1234 = c..., Format: Parquet'
    metadata={'DataFilters':'[status#ID = confirmed]'}
    assert complete_plan(a,metadata)==complete_plan(b,metadata)
    assert complete_plan(a,metadata)!=complete_plan(b,{'DataFilters':'[status#ID = cancelled]'})

@pytest.mark.parametrize('different',[False,True])
def test_executed_scan_metadata_checks_full_filters(tmp_path,different):
    import json
    from small_files.repeatability import scan_metadata
    (tmp_path/'events').mkdir();(tmp_path/'plans').mkdir()
    events=[]
    for layout in ('fragmented','compacted'):
        value='cancelled' if different and layout=='compacted' else 'confirmed'
        events.append({'Event':'org.apache.spark.sql.execution.ui.SparkListenerSQLExecutionStart',
            'sparkPlanInfo':{'metadata':{'Location':f'file:/data/{layout}',
                'ReadSchema':'struct<customer_id:bigint,region:string,amount_cents:bigint,status:string>',
                'PartitionFilters':'[]','DataFilters':f'[status#12 = {value}]'},'children':[]}})
    (tmp_path/'events'/'log').write_text('\n'.join(json.dumps(e) for e in events))
    if different:
        with pytest.raises(ValueError,match='metadata differs'):
            scan_metadata(tmp_path,1)
    else:
        assert scan_metadata(tmp_path,1)['selective']['compacted']['executions_checked']==1
