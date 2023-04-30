# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Example Airflow DAG that performs an export from BQ tables listed in
config file to GCS, copies GCS objects across locations (e.g., from US to
EU) then imports from GCS to BQ. The DAG imports the gcs_to_gcs operator
from plugins and dynamically builds the tasks based on the list of tables.
Lastly, the DAG defines a specific application logger to generate logs.

This DAG relies on three Airflow variables
https://airflow.apache.org/docs/apache-airflow/stable/concepts/variables.html:
* table_list_file_path - CSV file listing source and target tables, including
Datasets.
* gcs_source_bucket - Google Cloud Storage bucket to use for exporting
BigQuery tables in source.
* gcs_dest_bucket - Google Cloud Storage bucket to use for importing
BigQuery tables in destination.
See https://cloud.google.com/storage/docs/creating-buckets for creating a
bucket.
"""

# --------------------------------------------------------------------------------
# Load The Dependencies
# --------------------------------------------------------------------------------

import csv
import datetime
import io
import logging

from airflow import models
from airflow.contrib.operators import bigquery_to_gcs
from airflow.contrib.operators import gcs_to_bq
from airflow.contrib.operators import gcs_to_gcs
from airflow.operators import dummy_operator


# --------------------------------------------------------------------------------
# Set default arguments
# --------------------------------------------------------------------------------

# If you are running Airflow in more than one time zone
# see https://airflow.apache.org/docs/apache-airflow/stable/timezone.html
# for best practices
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)

default_args = {
    "owner": "airflow",
    "start_date": yesterday,
    "depends_on_past": False,
    "email": [""],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}

# --------------------------------------------------------------------------------
# Set variables
# --------------------------------------------------------------------------------


# Source Bucket
source_bucket = "{{var.value.gcs_source_bucket}}"

# Destination Bucket
dest_bucket = "{{var.value.gcs_dest_bucket}}"

# --------------------------------------------------------------------------------
# Set GCP logging
# --------------------------------------------------------------------------------

logger = logging.getLogger("bq_copy_us_to_eu_01")

# --------------------------------------------------------------------------------
# Functions
# --------------------------------------------------------------------------------


def read_table_list(table_list_file):
    """
    Reads the table list file that will help in creating Airflow tasks in
    the DAG dynamically.
    :param table_list_file: (String) The file location of the table list file,
    e.g. '/home/airflow/framework/table_list.csv'
    :return table_list: (List) List of tuples containing the source and
    target tables.
    """
    table_list = []
    logger.info(f"Reading table_list_file from : {str(table_list_file)}")
    try:
        with io.open(table_list_file, "rt", encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file)
            next(csv_reader)  # skip the headers
            for row in csv_reader:
                logger.info(row)
                table_tuple = {"table_source": row[0], "table_dest": row[1]}
                table_list.append(table_tuple)
            return table_list
    except IOError as e:
        logger.error(f"Error opening table_list_file {str(table_list_file)}: ", e)


# --------------------------------------------------------------------------------
# Main DAG
# --------------------------------------------------------------------------------

# Define a DAG (directed acyclic graph) of tasks.
# Any task you create within the context manager is automatically added to the
# DAG object.
with models.DAG(
    "composer_sample_bq_copy_across_locations",
    default_args=default_args,
    schedule_interval=None,
) as dag:
    start = dummy_operator.DummyOperator(task_id="start", trigger_rule="all_success")

    end = dummy_operator.DummyOperator(task_id="end", trigger_rule="all_success")
    # 'table_list_file_path': This variable will contain the location of the main
    # file. This is not part of an operator and cannot be templated, so it is included
    # inside of the DAG instead of with the templated variables above
    # to ensure the call to the DB only happens during DAG execution
    table_list_file_path = models.Variable.get("table_list_file_path")
    # Get the table list from main file
    all_records = read_table_list(table_list_file_path)

    # Loop over each record in the 'all_records' python list to build up
    # Airflow tasks
    for record in all_records:
        logger.info(f"Generating tasks to transfer table: {record}")

        table_source = record["table_source"]
        table_dest = record["table_dest"]

        BQ_to_GCS = bigquery_to_gcs.BigQueryToCloudStorageOperator(
            task_id=f'{table_source.replace(":", "_")}_BQ_to_GCS',
            source_project_dataset_table=table_source,
            destination_cloud_storage_uris=[
                f"gs://{source_bucket}/{table_source}-*.avro"
            ],
            export_format="AVRO",
        )

        GCS_to_GCS = gcs_to_gcs.GoogleCloudStorageToGoogleCloudStorageOperator(
            task_id=f'{table_source.replace(":", "_")}_GCS_to_GCS',
            source_bucket=source_bucket,
            source_object=f"{table_source}-*.avro",
            destination_bucket=dest_bucket,
        )

        GCS_to_BQ = gcs_to_bq.GoogleCloudStorageToBigQueryOperator(
            task_id=f'{table_dest.replace(":", "_")}_GCS_to_BQ',
            bucket=dest_bucket,
            source_objects=[f"{table_source}-*.avro"],
            destination_project_dataset_table=table_dest,
            source_format="AVRO",
            write_disposition="WRITE_TRUNCATE",
            autodetect=True,
        )

        start >> BQ_to_GCS >> GCS_to_GCS >> GCS_to_BQ >> end
