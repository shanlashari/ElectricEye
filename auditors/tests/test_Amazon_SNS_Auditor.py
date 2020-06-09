import datetime
import json
import os
import pytest
from botocore.stub import Stubber, ANY
from auditors.Amazon_SNS_Auditor import (
    CrossAccountCheck,
    sts,
    sns_client,
)

# not available in local testing without ECS
os.environ["AWS_REGION"] = "us-east-1"
# for local testing, don't assume default profile exists
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

sts_response = {
    "Account": "012345678901",
    "Arn": "arn:aws:iam::012345678901:user/user",
}

list_topics_response = {
    "Topics": [{"TopicArn": "arn:aws:sns:us-east-1:012345678901:MyTopic"},],
}

get_topic_attributes_response = {
    "Attributes": {
        "Policy": '{"Statement":[{"Principal":{"AWS":"arn:aws:iam::012345678901:root"},"Condition":{"StringEquals":{"AWS:SourceOwner":"805574742241"}}}]}',
    }
}


@pytest.fixture(scope="function")
def sts_stubber():
    sts_stubber = Stubber(sts)
    sts_stubber.activate()
    yield sts_stubber
    sts_stubber.deactivate()


@pytest.fixture(scope="function")
def sns_stubber():
    sns_stubber = Stubber(sns_client)
    sns_stubber.activate()
    yield sns_stubber
    sns_stubber.deactivate()


def test_principal_is_id_sns(sns_stubber, cloudwatch_stubber, sts_stubber):
    sts_stubber.add_response("get_caller_identity", sts_response)
    sns_stubber.add_response("list_topics", list_topics_response)
    sns_stubber.add_response("get_topic_attributes", get_topic_attributes_response)
    check = CrossAccountCheck()
    results = check.execute()
    for result in results:
        if "012345678901" in json.loads(result)["Statement"]["Principal"]["AWS"]:
            assert result["RecordState"] == "ARCHIVED"
        else:
            assert False
    sns_stubber.assert_no_pending_responses()
