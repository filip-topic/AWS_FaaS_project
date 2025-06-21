import boto3

# LocalStack endpoints
ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"  # Default region for LocalStack

# Dummy credentials for LocalStack
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

# Resource names
S3_INPUT_BUCKET = "reviews-input"
S3_PROCESSED_BUCKET = "reviews-processed"
DDB_REVIEW_METADATA = "review-metadata"
DDB_CUSTOMER_STATS = "customer-stats"

# SSM parameter names
SSM_PARAMS = {
    "input_bucket": "/dic2025/a3/bucket/input",
    "processed_bucket": "/dic2025/a3/bucket/processed",
    "review_metadata_table": "/dic2025/a3/table/review_metadata",
    "customer_stats_table": "/dic2025/a3/table/customer_stats"
}

def reset_s3(s3, bucket):
    try:
        # Delete all objects
        resp = s3.list_objects_v2(Bucket=bucket)
        for obj in resp.get("Contents", []):
            s3.delete_object(Bucket=bucket, Key=obj["Key"])
        s3.delete_bucket(Bucket=bucket)
        print(f"Deleted bucket: {bucket}")
    except s3.exceptions.NoSuchBucket:
        pass

    s3.create_bucket(Bucket=bucket)
    print(f"Created bucket: {bucket}")

def reset_ddb(ddb, table_name, key_schema, attr_defs):
    try:
        ddb.delete_table(TableName=table_name)
        waiter = ddb.get_waiter('table_not_exists')
        waiter.wait(TableName=table_name)
        print(f"Deleted table: {table_name}")
    except ddb.exceptions.ResourceNotFoundException:
        pass

    ddb.create_table(
        TableName=table_name,
        KeySchema=key_schema,
        AttributeDefinitions=attr_defs,
        BillingMode='PAY_PER_REQUEST'
    )
    waiter = ddb.get_waiter('table_exists')
    waiter.wait(TableName=table_name)
    print(f"Created table: {table_name}")

def put_ssm_param(ssm, name, value):
    ssm.put_parameter(
        Name=name,
        Value=value,
        Type="String",
        Overwrite=True
    )
    print(f"Set SSM param: {name} = {value}")

def main():
    s3 = boto3.client(
        "s3", 
        endpoint_url=ENDPOINT_URL, 
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    ddb = boto3.client(
        "dynamodb", 
        endpoint_url=ENDPOINT_URL, 
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    ssm = boto3.client(
        "ssm", 
        endpoint_url=ENDPOINT_URL, 
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    # S3 buckets
    reset_s3(s3, S3_INPUT_BUCKET)
    reset_s3(s3, S3_PROCESSED_BUCKET)

    # DynamoDB tables
    reset_ddb(
        ddb, DDB_REVIEW_METADATA,
        key_schema=[
            {"AttributeName": "customerId", "KeyType": "HASH"},
            {"AttributeName": "reviewId", "KeyType": "RANGE"}
        ],
        attr_defs=[
            {"AttributeName": "customerId", "AttributeType": "S"},
            {"AttributeName": "reviewId", "AttributeType": "S"}
        ]
    )
    reset_ddb(
        ddb, DDB_CUSTOMER_STATS,
        key_schema=[
            {"AttributeName": "customerId", "KeyType": "HASH"}
        ],
        attr_defs=[
            {"AttributeName": "customerId", "AttributeType": "S"}
        ]
    )

    # SSM parameters
    put_ssm_param(ssm, SSM_PARAMS["input_bucket"], S3_INPUT_BUCKET)
    put_ssm_param(ssm, SSM_PARAMS["processed_bucket"], S3_PROCESSED_BUCKET)
    put_ssm_param(ssm, SSM_PARAMS["review_metadata_table"], DDB_REVIEW_METADATA)
    put_ssm_param(ssm, SSM_PARAMS["customer_stats_table"], DDB_CUSTOMER_STATS)

if __name__ == "__main__":
    main()