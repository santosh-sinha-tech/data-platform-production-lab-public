import pytest
from pyspark.sql import SparkSession
from small_files.data import generate, fingerprint, write_layout, read
from small_files.model import file_stats
from small_files.cli import query, output_digest, event_metrics

@pytest.fixture(scope='module')
def spark():
    s=(SparkSession.builder.master('local[2]').appName('lab-tests')
       .config('spark.sql.session.timeZone','UTC').config('spark.ui.enabled','false')
       .config('spark.sql.shuffle.partitions','2').getOrCreate())
    s.sparkContext.setLogLevel('ERROR')
    yield s
    s.stop()

def test_generation(spark):
    a=generate(spark,1000,42,2)
    assert fingerprint(a)==fingerprint(a.repartition(3))
    # event_bucket intentionally depends on partition count; repartitioning execution does not.
    assert fingerprint(a)==fingerprint(generate(spark,1000,42,2))
    assert fingerprint(a)!=fingerprint(generate(spark,1000,43,2))

@pytest.mark.parametrize('partitioned',[True,False])
def test_equivalence_and_queries(spark,tmp_path,partitioned):
    source=generate(spark,1000,42,2)
    f,c=tmp_path/'fragmented',tmp_path/'compacted'
    write_layout(source,f,8,2,partitioned)
    write_layout(read(spark,f),c,2,2,partitioned)
    assert fingerprint(source)==fingerprint(read(spark,f))==fingerprint(read(spark,c))
    assert file_stats(f)['files']>file_stats(c)['files']
    for name in ('full_aggregation','selective','partition_pruned'):
        assert output_digest(query(read(spark,f),name).collect())==output_digest(query(read(spark,c),name).collect())
    assert fingerprint(source.filter('event_id>0'))!=fingerprint(source)
    assert fingerprint(source.withColumn('amount_cents', source.amount_cents + 1))!=fingerprint(source)

def test_missing(spark,tmp_path):
    with pytest.raises(FileNotFoundError):
        read(spark,tmp_path/'missing')

def test_event_parser(tmp_path):
    (tmp_path/'events').write_text('{"Event":"SparkListenerTaskEnd","Task End Reason":{"Reason":"Success"},"Task Metrics":{"Input Metrics":{"Bytes Read":123,"Records Read":4}}}\n')
    result=event_metrics(tmp_path)
    assert result['input_bytes']==123 and result['successful_task_attempts']==1
