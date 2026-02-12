"""
AWS Test Utilities
Helper functions for AWS integration tests
"""
import boto3
import json
import os
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError


def get_aws_session(profile: str = 'tmf-dev', region: str = 'us-east-1') -> boto3.Session:
    """Create AWS session with profile"""
    return boto3.Session(profile_name=profile, region_name=region)


def get_terraform_outputs(iac_dir: str = '../../../iac/aws') -> Dict[str, Any]:
    """Load Terraform outputs from state or JSON"""
    state_file = os.path.join(iac_dir, 'terraform.tfstate')
    
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
            return {
                key: value['value']
                for key, value in state.get('outputs', {}).items()
            }
    
    raise FileNotFoundError(f"Terraform state not found at {state_file}")


def get_s3_object_content(bucket: str, key: str, profile: str = 'tmf-dev') -> Dict[str, Any]:
    """Retrieve and parse S3 object as JSON"""
    session = get_aws_session(profile)
    s3 = session.client('s3')
    
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise FileNotFoundError(f"S3 object not found: s3://{bucket}/{key}")
        raise


def list_s3_objects_by_prefix(bucket: str, prefix: str, profile: str = 'tmf-dev') -> list:
    """List S3 objects with prefix"""
    session = get_aws_session(profile)
    s3 = session.client('s3')
    
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
    
    objects = []
    for page in pages:
        if 'Contents' in page:
            objects.extend(page['Contents'])
    
    return objects


def delete_s3_objects(bucket: str, prefix: str, profile: str = 'tmf-dev') -> int:
    """Delete all S3 objects with prefix (for test cleanup)"""
    objects = list_s3_objects_by_prefix(bucket, prefix, profile)
    
    if not objects:
        return 0
    
    session = get_aws_session(profile)
    s3 = session.client('s3')
    
    delete_keys = [{'Key': obj['Key']} for obj in objects]
    response = s3.delete_objects(
        Bucket=bucket,
        Delete={'Objects': delete_keys}
    )
    
    return len(response.get('Deleted', []))


def get_lambda_logs(function_name: str, profile: str = 'tmf-dev', limit: int = 10) -> list:
    """Get recent Lambda CloudWatch logs"""
    session = get_aws_session(profile)
    logs = session.client('logs')
    
    log_group = f'/aws/lambda/{function_name}'
    
    try:
        streams = logs.describe_log_streams(
            logGroupName=log_group,
            orderBy='LastEventTime',
            descending=True,
            limit=5
        )
        
        events = []
        for stream in streams['logStreams']:
            stream_events = logs.get_log_events(
                logGroupName=log_group,
                logStreamName=stream['logStreamName'],
                limit=limit
            )
            events.extend(stream_events['events'])
        
        return sorted(events, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return []
        raise


def invoke_lambda(
    function_name: str,
    payload: Dict[str, Any],
    profile: str = 'tmf-dev'
) -> Dict[str, Any]:
    """Invoke Lambda function directly (not via API Gateway)"""
    session = get_aws_session(profile)
    lambda_client = session.client('lambda')
    
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    return result


def wait_for_s3_object(
    bucket: str,
    key: str,
    profile: str = 'tmf-dev',
    max_attempts: int = 10,
    delay: int = 1
) -> bool:
    """Wait for S3 object to exist (eventual consistency)"""
    import time
    
    session = get_aws_session(profile)
    s3 = session.client('s3')
    
    for attempt in range(max_attempts):
        try:
            s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                continue
            raise
    
    return False
