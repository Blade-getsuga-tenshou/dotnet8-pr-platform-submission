# Fabric notebook export (bronze_load): Bronze, Silver, and Gold layers.
# Run in a Fabric lakehouse with dora_metrics.xlsx uploaded to Files.
# Output matches the local pipeline in pipeline/run_pipeline.py.

import pandas as pd
from datetime import datetime, timezone

src = "/lakehouse/default/Files/dora_metrics.xlsx"
sheets = pd.read_excel(src, sheet_name=None, engine="openpyxl")
loaded_at = datetime.now(timezone.utc).isoformat()

for name, df in sheets.items():
    raw = df.astype(object).where(df.notna(), None).map(lambda v: None if v is None else str(v))
    raw["_source_file"] = "dora_metrics.xlsx"
    raw["_source_sheet"] = name
    raw["_loaded_at_utc"] = loaded_at
    sdf = spark.createDataFrame(raw)
    sdf.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"bronze_{name}")
    print(f"bronze_{name}: {sdf.count()} rows")

# ---- Silver ----
from pyspark.sql import functions as F

c = spark.table("bronze_commits")
b = spark.table("bronze_builds")
i = spark.table("bronze_incidents")

silver_commits = (c.dropDuplicates(["commit_id", "build_sk"])
    .withColumn("build_sk", F.col("build_sk").cast("long"))
    .withColumn("author_date", F.to_timestamp("author_date"))
    .withColumn("committer_date", F.to_timestamp("committer_date")))

silver_builds = (b.dropDuplicates(["build_id"])
    .withColumn("build_id", F.col("build_id").cast("long"))
    .withColumn("pipeline_start_time", F.to_timestamp("pipeline_start_time"))
    .withColumn("pipeline_end_time", F.to_timestamp("pipeline_end_time")))

ts_cols = ["incident_started_datetime", "incident_reported_customersupport_datetime",
           "incident_reported_engineering_datetime", "investigation_started_datetime",
           "incident_resolved_datetime"]
silver_incidents = (i.dropDuplicates(["workitem_id"])
    .withColumn("workitem_id", F.col("workitem_id").cast("long"))
    .withColumn("caused_by_deployment", F.col("caused_by_deployment").cast("int")))
for col in ts_cols:
    silver_incidents = silver_incidents.withColumn(col, F.to_timestamp(col))

for name, df in [("silver_commits", silver_commits),
                 ("silver_builds", silver_builds),
                 ("silver_incidents", silver_incidents)]:
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(name)
    print(f"{name}: {df.count()} rows")

dq1 = spark.table("silver_incidents").filter(
    (F.col("incident_resolved_datetime") < F.col("incident_started_datetime")) |
    (F.col("incident_resolved_datetime") < F.col("incident_reported_engineering_datetime"))
)
dq1.select("workitem_id", "title", "incident_started_datetime", "incident_resolved_datetime").show()

# ---- Gold ----
commits = spark.table("silver_commits")
builds = spark.table("silver_builds").dropna(subset=["pipeline_end_time"])

# DQ1 rule: incidents that fail the timeline check are excluded from Gold.
dq1_ids = [r["workitem_id"] for r in spark.table("silver_incidents").filter(
    (F.col("incident_resolved_datetime") < F.col("incident_started_datetime")) |
    (F.col("incident_resolved_datetime") < F.col("incident_reported_engineering_datetime"))
).select("workitem_id").collect()]
incidents = spark.table("silver_incidents").filter(~F.col("workitem_id").isin(dq1_ids))

first_commit = (commits.dropna(subset=["build_sk"])
    .groupBy("build_sk").agg(F.min("committer_date").alias("first_commit_time")))

builds = (builds.join(first_commit, builds.build_id == first_commit.build_sk, "left")
    .withColumn("lead_time_hours",
        (F.unix_timestamp("pipeline_end_time") - F.unix_timestamp("first_commit_time")) / 3600))

negative_lead = builds.filter(F.col("lead_time_hours") < 0).count()
builds = builds.withColumn("lead_time_hours",
    F.when(F.col("lead_time_hours") < 0, None).otherwise(F.col("lead_time_hours")))

builds = builds.withColumn("week", F.date_sub(F.to_date("pipeline_end_time"),
    F.dayofweek("pipeline_end_time") - 2))
incidents = incidents.withColumn("week", F.date_sub(F.to_date("incident_started_datetime"),
    F.dayofweek("incident_started_datetime") - 2))
incidents = incidents.withColumn("time_to_restore_hours",
    (F.unix_timestamp("incident_resolved_datetime") - F.unix_timestamp("incident_started_datetime")) / 3600)

dep_weekly = builds.groupBy("week").agg(
    F.count("build_id").alias("deployments"),
    F.percentile_approx("lead_time_hours", 0.5).alias("median_lead_time_hours"))
inc_weekly = incidents.groupBy("week").agg(
    F.count("workitem_id").alias("incidents"),
    F.sum("caused_by_deployment").alias("caused_by_deployment"))
weekly = (dep_weekly.join(inc_weekly, "week", "full_outer")
    .fillna({"deployments": 0, "incidents": 0, "caused_by_deployment": 0})
    .withColumn("change_failure_rate",
        F.when(F.col("deployments") > 0, F.col("caused_by_deployment") / F.col("deployments"))))
weekly.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("gold_dora_weekly")

n_builds = builds.count()
bounds = builds.agg(F.min(F.to_date("pipeline_end_time")).alias("first"),
                    F.max(F.to_date("pipeline_end_time")).alias("last")).collect()[0]
window_days = (bounds["last"] - bounds["first"]).days + 1
summary = {
    "deployment_frequency_per_day": n_builds / window_days,
    "median_lead_time_hours": builds.agg(F.percentile_approx("lead_time_hours", 0.5)).collect()[0][0],
    "change_failure_rate": incidents.agg(F.sum("caused_by_deployment")).collect()[0][0] / n_builds,
    "median_time_to_restore_hours": incidents.agg(F.percentile_approx("time_to_restore_hours", 0.5)).collect()[0][0],
    "mean_time_to_restore_hours": incidents.agg(F.avg("time_to_restore_hours")).collect()[0][0],
    "deployments_counted": n_builds,
    "incidents_included": incidents.count(),
    "lead_time_negative_excluded": negative_lead,
    "window_days": window_days,
}
for k, v in summary.items():
    print(f"{k}: {v}")