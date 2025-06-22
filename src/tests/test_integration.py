import pytest
import json
import time
import uuid

# Use pytest fixtures for AWS clients
@pytest.mark.usefixtures("aws_credentials", "s3_client", "ddb_client", "lambda_client")
class TestReviewPipeline:
    INPUT_BUCKET = "reviews-input"
    PROCESSED_BUCKET = "reviews-processed"
    REVIEW_TABLE = "review-metadata"
    STATS_TABLE = "customer-stats"

    def unique_ids(self):
        customer_id = f"test_customer_{uuid.uuid4()}"
        review_id = f"review_{uuid.uuid4()}"
        key = f"review_{uuid.uuid4()}.json"
        return customer_id, review_id, key

    def upload_review(self, s3_client, customer_id, review_id, key, review_text, summary="Test summary", overall=5):
        review = {
            "customerId": customer_id,
            "reviewId": review_id,
            "summary": summary,
            "reviewText": review_text,
            "overall": overall
        }
        s3_client.put_object(
            Bucket=self.INPUT_BUCKET,
            Key=key,
            Body=json.dumps(review).encode('utf-8'),
            ContentType="application/json"
        )

    def cleanup(self, s3_client, ddb_client, customer_id, review_id, key):
        try:
            s3_client.delete_object(Bucket=self.INPUT_BUCKET, Key=key)
        except Exception:
            pass
        try:
            s3_client.delete_object(Bucket=self.PROCESSED_BUCKET, Key=key)
        except Exception:
            pass
        try:
            ddb_client.delete_item(
                TableName=self.REVIEW_TABLE,
                Key={"customerId": {"S": customer_id}, "reviewId": {"S": review_id}}
            )
        except Exception:
            pass
        try:
            ddb_client.delete_item(
                TableName=self.STATS_TABLE,
                Key={"customerId": {"S": customer_id}}
            )
        except Exception:
            pass

    def wait_for_s3(self, s3_client, bucket, key, timeout=15):
        for _ in range(timeout):
            try:
                s3_client.head_object(Bucket=bucket, Key=key)
                return True
            except Exception:
                time.sleep(1)
        return False

    def wait_for_ddb(self, ddb_client, table, key, attr=None, timeout=30):
        for _ in range(timeout):
            try:
                resp = ddb_client.get_item(TableName=table, Key=key)
                if "Item" in resp:
                    if attr is None or attr in resp["Item"]:
                        return resp["Item"]
            except Exception:
                pass
            time.sleep(1)
        # Final fetch for debug
        try:
            resp = ddb_client.get_item(TableName=table, Key=key)
            if "Item" in resp:
                print(f"[DEBUG] Item found in {table} but missing attr '{attr}': {resp['Item']}")
        except Exception as e:
            print(f"[DEBUG] Error fetching item from {table}: {e}")
        return None

    def test_preprocessing_lambda_trigger(self, s3_client, ddb_client):
        customer_id, review_id, key = self.unique_ids()
        self.upload_review(s3_client, customer_id, review_id, key, "Clean review text.")
        assert self.wait_for_s3(s3_client, self.PROCESSED_BUCKET, key), "Preprocessing output not found in processed bucket."
        obj = s3_client.get_object(Bucket=self.PROCESSED_BUCKET, Key=key)
        processed = json.loads(obj["Body"].read())
        assert "summary_clean" in processed and "reviewText_clean" in processed
        self.cleanup(s3_client, ddb_client, customer_id, review_id, key)

    def test_profanity_detection(self, s3_client, ddb_client):
        customer_id, review_id, key = self.unique_ids()
        self.upload_review(s3_client, customer_id, review_id, key, "This is a fucking bad review, shit.")
        assert self.wait_for_ddb(ddb_client, self.REVIEW_TABLE, {"customerId": {"S": customer_id}, "reviewId": {"S": review_id}}, attr="isUnpolite"), "Profanity check did not update review metadata."
        item = self.wait_for_ddb(ddb_client, self.STATS_TABLE, {"customerId": {"S": customer_id}}, attr="unpoliteCount")
        assert item and int(item["unpoliteCount"]["N"]) >= 1
        self.cleanup(s3_client, ddb_client, customer_id, review_id, key)

    def test_sentiment_analysis(self, s3_client, ddb_client):
        customer_id, review_id, key = self.unique_ids()
        self.upload_review(s3_client, customer_id, review_id, key, "I love this product!")
        # Wait for item to exist first
        item = self.wait_for_ddb(ddb_client, self.REVIEW_TABLE, {"customerId": {"S": customer_id}, "reviewId": {"S": review_id}})
        assert item, "Review metadata item not created."
        # Now wait for sentiment
        item = self.wait_for_ddb(ddb_client, self.REVIEW_TABLE, {"customerId": {"S": customer_id}, "reviewId": {"S": review_id}}, attr="sentiment")
        assert item and "sentiment" in item, "Sentiment not stored in review metadata."
        self.cleanup(s3_client, ddb_client, customer_id, review_id, key)

    def test_customer_banning(self, s3_client, ddb_client):
        customer_id = f"test_customer_{uuid.uuid4()}"
        review_ids = [f"review_{uuid.uuid4()}" for _ in range(4)]
        keys = [f"review_{uuid.uuid4()}.json" for _ in range(4)]
        for i in range(4):
            self.upload_review(s3_client, customer_id, review_ids[i], keys[i], "This is a fucking bad review, shit.")
            assert self.wait_for_ddb(ddb_client, self.REVIEW_TABLE, {"customerId": {"S": customer_id}, "reviewId": {"S": review_ids[i]}}, attr="isUnpolite")
        item = self.wait_for_ddb(ddb_client, self.STATS_TABLE, {"customerId": {"S": customer_id}}, attr="banned")
        assert item and item["banned"]["BOOL"] is True, "Customer should be banned after >3 unpolite reviews."
        for i in range(4):
            self.cleanup(s3_client, ddb_client, customer_id, review_ids[i], keys[i])

    def test_full_pipeline_integration(self, s3_client, ddb_client):
        customer_id, review_id, key = self.unique_ids()
        self.upload_review(s3_client, customer_id, review_id, key, "This is a fucking bad product. I hate it.")
        # Wait for all outputs
        assert self.wait_for_s3(s3_client, self.PROCESSED_BUCKET, key), "Preprocessing output not found."
        # Wait for item to exist first
        item = self.wait_for_ddb(ddb_client, self.REVIEW_TABLE, {"customerId": {"S": customer_id}, "reviewId": {"S": review_id}})
        assert item, "Review metadata item not created."
        # Wait for isUnpolite
        item = self.wait_for_ddb(ddb_client, self.REVIEW_TABLE, {"customerId": {"S": customer_id}, "reviewId": {"S": review_id}}, attr="isUnpolite")
        assert item and "isUnpolite" in item, "Profanity not detected."
        # Wait for sentiment
        item = self.wait_for_ddb(ddb_client, self.REVIEW_TABLE, {"customerId": {"S": customer_id}, "reviewId": {"S": review_id}}, attr="sentiment")
        assert item and "sentiment" in item, "Sentiment not stored."
        stats = self.wait_for_ddb(ddb_client, self.STATS_TABLE, {"customerId": {"S": customer_id}}, attr="unpoliteCount")
        assert stats and int(stats["unpoliteCount"]["N"]) >= 1
        self.cleanup(s3_client, ddb_client, customer_id, review_id, key) 