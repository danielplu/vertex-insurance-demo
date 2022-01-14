# Copyright 2017-2021 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import logging
from datetime import datetime
import tensorflow as tf

from google.cloud import aiplatform
from google.cloud.aiplatform import gapic as aip
from google.cloud.aiplatform import hyperparameter_tuning as hpt
from kfp.v2 import compiler, dsl

ENDPOINT_NAME = 'insurance'

def train_automl_model(data_set, timestamp, develop_mode):
    # train
    model_display_name = '{}-{}'.format(ENDPOINT_NAME, timestamp)
    job = aiplatform.AutoMLTabularTrainingJob(
        display_name='train-{}'.format(model_display_name),
        optimization_prediction_type='regression'
    )
    model = job.run(
        dataset=data_set,
        # See https://googleapis.dev/python/aiplatform/latest/aiplatform.html#
        #predefined_split_column_name='data_split',
        target_column='charges',
        model_display_name=model_display_name,
        budget_milli_node_hours=(300 if develop_mode else 2000),
        disable_early_stopping=False,
        export_evaluated_data_items=True,
        sync=develop_mode
    )
    return model

def main():
    aiplatform.init(project=PROJECT, location=REGION)

    # create data set
    data_set = aiplatform.TabularDataset.create(
        display_name='data-{}'.format(ENDPOINT_NAME),
        bq_source='bq://devproject-337319.tokenized_data.insurance'
    )
    # train
    if AUTOML:
        model = train_automl_model(data_set, TIMESTAMP, DEVELOP_MODE)

    # create endpoint if it doesn't already exist
    endpoints = aiplatform.Endpoint.list(
        filter='display_name="{}"'.format(ENDPOINT_NAME),
        order_by='create_time desc',
        project=PROJECT, location=REGION,
    )
    if len(endpoints) > 0:
        endpoint = endpoints[0]  # most recently created
    else:
        endpoint = aiplatform.Endpoint.create(
            display_name=ENDPOINT_NAME, project=PROJECT, location=REGION,
            sync=DEVELOP_MODE
        )

    # deploy
    model.deploy(
        endpoint=endpoint,
        traffic_split={"0": 100},
        machine_type='n1-standard-2',
        min_replica_count=1,
        max_replica_count=1,
        sync=DEVELOP_MODE
    )

    if DEVELOP_MODE:
        model.wait()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        '--region',
        help='Where to run the trainer',
        default='us-central1'
    )
    parser.add_argument(
        '--project',
        help='Project to be billed',
        required=True
    )
    parser.add_argument(
        '--develop',
        help='Train on a small subset in development',
        dest='develop',
        action='store_true')
    parser.set_defaults(develop=False)
    parser.add_argument(
        '--automl',
        help='Train an AutoML Table, instead of using model.py',
        dest='automl',
        action='store_true')
    parser.set_defaults(automl=False)

    # parse args
    logging.getLogger().setLevel(logging.INFO)
    args = parser.parse_args().__dict__
    PROJECT = args['project']
    REGION = args['region']
    DEVELOP_MODE = args['develop']
    AUTOML = args['automl']
    TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")

    main()
