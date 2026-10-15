"""Airflow owns execution status; the quality result owns data readiness."""

import pendulum
from airflow.sdk import dag, task

from booking_pipeline.generator import generate
from booking_pipeline.publication import route
from booking_pipeline.quality import evaluate
from booking_pipeline.runtime import spark_session
from booking_pipeline.transformation import transform


@dag(dag_id="booking_readiness", schedule=None,
     start_date=pendulum.datetime(2026, 1, 1, tz="UTC"), catchup=False,
     max_active_runs=1, default_args={"retries": 0},
     tags=["reference-implementation", "data-quality"])
def booking_readiness():
    @task
    def synthetic_source(**context):
        conf = context["dag_run"].conf
        spark = spark_session()
        try:
            generate(spark, conf["data_root"], conf["run_id"], conf["scenario"], conf["contract_path"])
        finally:
            spark.stop()
        # XCom contains identifiers and paths, never booking data.
        return {"data_root": conf["data_root"], "run_id": conf["run_id"]}

    @task
    def pyspark_transformation(run):
        spark = spark_session()
        try:
            transform(spark, run["data_root"], run["run_id"])
        finally:
            spark.stop()
        return run

    @task
    def data_quality_gate(run):
        spark = spark_session()
        try:
            evaluate(spark, run["data_root"], run["run_id"])
        finally:
            spark.stop()
        return run

    @task
    def publication_router(run):
        route(run["data_root"], run["run_id"])

    publication_router(data_quality_gate(pyspark_transformation(synthetic_source())))


dag = booking_readiness()
