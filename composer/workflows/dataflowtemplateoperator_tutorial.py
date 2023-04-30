# Copyright 2020 Google LLC
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

# [START composer_dataflow_dag]


"""Example Airflow DAG that creates a Cloud Dataflow workflow which takes a
text file and adds the rows to a BigQuery table.

This DAG relies on four Airflow variables
https://airflow.apache.org/docs/apache-airflow/stable/concepts/variables.html
* project_id - Google Cloud Project ID to use for the Cloud Dataflow cluster.
* gce_zone - Google Compute Engine zone where Cloud Dataflow cluster should be
  created.
For more info on zones where Dataflow is available see:
https://cloud.google.com/dataflow/docs/resources/locations
* bucket_path - Google Cloud Storage bucket where you've stored the User Defined
Function (.js), the input file (.txt), and the JSON schema (.json).
"""


import datetime

from airflow import models
from airflow.providers.google.cloud.operators.dataflow import (
    DataflowTemplatedJobStartOperator,
)
from airflow.utils.dates import days_ago

bucket_path = "{{var.value.bucket_path}}"
project_id = "{{var.value.project_id}}"
gce_zone = "{{var.value.gce_zone}}"


default_args = {
    "start_date": days_ago(1),
    "dataflow_default_options": {
        "project": project_id,
        "zone": gce_zone,
        "tempLocation": f"{bucket_path}/tmp/",
    },
}

# Define a DAG (directed acyclic graph) of tasks.
# Any task you create within the context manager is automatically added to the
# DAG object.
with models.DAG(
    # The id you will see in the DAG airflow page
    "composer_dataflow_dag",
    default_args=default_args,
    # The interval with which to schedule the DAG
    schedule_interval=datetime.timedelta(days=1),  # Override to match your needs
) as dag:

    start_template_job = DataflowTemplatedJobStartOperator(
        task_id="dataflow_operator_transform_csv_to_bq",
        template="gs://dataflow-templates/latest/GCS_Text_to_BigQuery",
        parameters={
            "javascriptTextTransformFunctionName": "transformCSVtoJSON",
            "JSONPath": f"{bucket_path}/jsonSchema.json",
            "javascriptTextTransformGcsPath": f"{bucket_path}/transformCSVtoJSON.js",
            "inputFilePattern": f"{bucket_path}/inputFile.txt",
            "outputTable": f"{project_id}:average_weather.average_weather",
            "bigQueryLoadingTemporaryDirectory": f"{bucket_path}/tmp/",
        },
    )

# [END composer_dataflow_dag]
