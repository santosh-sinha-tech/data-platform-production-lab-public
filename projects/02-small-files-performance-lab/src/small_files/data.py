"""Deterministic SQL expressions avoid random stream/partition dependence."""
from pathlib import Path
from pyspark.sql import DataFrame, SparkSession, functions as F

def generate(spark: SparkSession, rows: int, seed: int, partitions: int) -> DataFrame:
    df = spark.range(rows, numPartitions=partitions)
    return df.selectExpr("id AS event_id",
        f"timestamp_seconds(1704067200 + pmod(xxhash64(id, {seed}), 31536000)) AS event_timestamp",
        f"pmod(xxhash64(id, {seed+1}), 100000) AS customer_id",
        f"element_at(array('APAC','EMEA','AMER','LATAM'), cast(pmod(xxhash64(id, {seed+3}),4)+1 as int)) AS region",
        f"cast(pmod(xxhash64(id, {seed+2}), 1000000) as bigint) AS amount_cents",
        "element_at(array('confirmed','cancelled','pending'), cast(pmod(id,3)+1 as int)) AS status",
        f"cast(pmod(id, {partitions}) as int) AS event_bucket")

def fingerprint(df: DataFrame) -> dict:
    # Decimal sums avoid long overflow; two independently salted row hashes reduce collisions.
    cols = [F.col(c) for c in sorted(df.columns)]
    return df.agg(F.count('*').alias('rows'),
        F.sum('amount_cents').alias('amount_cents'),
        F.sum(F.xxhash64(*cols).cast('decimal(38,0)')).alias('hash_sum_1'),
        F.sum(F.xxhash64(F.lit(7919), *cols).cast('decimal(38,0)')).alias('hash_sum_2')).first().asDict()

def write_layout(df: DataFrame, path: Path, target: int, buckets: int, partitioned: bool) -> None:
    # Controlled per-bucket writes: target is still verified from filesystem afterward.
    if partitioned:
        for bucket in range(buckets):
            (df.filter(F.col('event_bucket') == bucket).drop('event_bucket')
             .repartition(target // buckets).write.mode('errorifexists')
             .option('compression','snappy').parquet(str(path / f'event_bucket={bucket}')))
    else:
        df.repartition(target).write.mode('errorifexists').option('compression','snappy').parquet(str(path))

def read(spark: SparkSession, path: Path) -> DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return spark.read.parquet(str(path))
