"""Normalize received bookings without filling, dropping, or inventing rows."""

from pyspark.sql import functions as F

from booking_pipeline.observability import emit
from booking_pipeline.runtime import run_path


def transform(spark, root, run_id):
    source = run_path(root, "incoming", run_id) / "bookings"
    target = run_path(root, "processed", run_id)
    bookings = spark.read.parquet(str(source))
    normalized = (bookings
                  .withColumn("currency", F.upper(F.trim("currency")))
                  .withColumn("booking_status", F.upper(F.trim("booking_status")))
                  .withColumn("booking_amount", F.col("booking_amount").cast("decimal(18,2)")))
    normalized.write.mode("errorifexists").parquet(str(target))
    emit("transformation_completed", run_id=run_id, transformation_status="SUCCESS")
    return run_id
