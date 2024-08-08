import unittest
import json
import os
from server import app, dynamodb, s3, TABLE_NAME, BUCKET_NAME

# Set dummy AWS credentials and region for testing
os.environ['AWS_ACCESS_KEY_ID'] = 'fake_access_key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fake_secret_key'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['DYNAMODB_ENDPOINT_URL'] = 'http://localstack:4566'
os.environ['S3_ENDPOINT_URL'] = 'http://localstack:4566'

class FlaskTestCase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up the LocalStack resources."""
        try:
            # Check if the table exists before creating
            tables = dynamodb.tables.all()
            table_names = [table.name for table in tables]
            
            if TABLE_NAME not in table_names:
                table = dynamodb.create_table(
                    TableName=TABLE_NAME,
                    KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
                    AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
                    ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
                )
                table.wait_until_exists()
        except Exception as e:
            print(f"Error setting up LocalStack resources: {e}")

        try:
            s3.create_bucket(Bucket=BUCKET_NAME)
        except s3.exceptions.BucketAlreadyOwnedByYou:
            pass
    
    @classmethod
    def tearDownClass(cls):
        """Tear down the LocalStack resources."""
        try:
            # Delete all objects in the bucket
            bucket_objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
            if 'Contents' in bucket_objects:
                for obj in bucket_objects['Contents']:
                    s3.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])
            
            # Now delete the bucket
            s3.delete_bucket(Bucket=BUCKET_NAME)
        except Exception as e:
            print(f"Error deleting S3 bucket: {e}")
        
        try:
            dynamodb.Table(TABLE_NAME).delete()
        except Exception as e:
            print(f"Error deleting DynamoDB table: {e}")
    
    def setUp(self):
        self.app = app.test_client(self)
        self.app.testing = True

    def test_get(self):
        response = self.app.get('/get')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

    def test_get_with_params(self):
        response = self.app.post('/post', json={'message': 'Test message'})
        message_id = response.json['id']
        
        response = self.app.get(f'/get/{message_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], 'Test message')

    def test_get_with_no_results(self):
        response = self.app.get('/get/nonexistent_id')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {'error': 'Message not found'})

    def test_get_with_no_parameters(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode('utf-8'), 'Hello World!')

    def test_post(self):
        response = self.app.post('/post', json={'message': 'Hello, Isha!'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('response', response.json)
        self.assertIn('id', response.json)

    def test_post_duplicate(self):
        response = self.app.post('/post', json={'message': 'Duplicate message'})
        first_id = response.json['id']
        
        response = self.app.post('/post', json={'message': 'Duplicate message'})
        second_id = response.json['id']
        
        self.assertNotEqual(first_id, second_id)

    def test_put(self):
        # First, post a message
        post_response = self.app.post('/post', json={'message': 'Initial message'})
        message_id = post_response.json['id']
        
        # Now, update the message
        new_message = 'Updated message'
        response = self.app.put(f'/put/{message_id}', data=json.dumps({'message': new_message}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'response': 'Yayy! Updated!'})

        # Verify the update
        response = self.app.get(f'/get/{message_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['message'], new_message)

    def test_put_with_no_valid_target(self):
        response = self.app.put('/put/nonexistent_id', data=json.dumps({'message': 'Message'}), content_type='application/json')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {'error': 'Message not found'})

    def test_delete(self):
        # First, post a message
        post_response = self.app.post('/post', json={'message': 'Message to delete'})
        message_id = post_response.json['id']
        
        # Delete the message
        response = self.app.delete(f'/delete/{message_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'response': 'Yayy! Message deleted!'})

        # Verify the deletion
        response = self.app.get(f'/get/{message_id}')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json, {'error': 'Message not found'})

    def test_delete_with_no_valid_target(self):
        response = self.app.delete('/delete/nonexistent_id')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'response': 'Yayy! Message deleted!'})

if __name__ == '__main__':
    unittest.main()