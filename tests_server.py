import unittest
import json
import os
from server import app, dynamodb, s3, TABLE_NAME, BUCKET_NAME

# Set dummy AWS credentials and region for testing
os.environ['AWS_ACCESS_KEY_ID'] = 'fake_access_key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'fake_secret_key'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

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
            dynamodb.Table(TABLE_NAME).delete()
        except Exception as e:
            print(f"Error deleting DynamoDB table: {e}")
        
        try:
            s3.delete_bucket(Bucket=BUCKET_NAME)
        except Exception as e:
            print(f"Error deleting S3 bucket: {e}")
    
    def setUp(self):
        self.app = app.test_client(self)
        self.app.testing = True

    def test_get(self):
        response = self.app.get('/get')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

    def test_post(self):
        response = self.app.post('/post', json={'message': 'Hello, Isha!'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'response': 'You sent: Hello, Isha!'})

    def test_put(self):
        # First, post a message
        self.app.post('/post', json={'message': 'Initial message'})
        
        # Now, update the message
        new_message = 'Updated message'
        response = self.app.put('/put', data=json.dumps({'message': new_message}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'response': 'Yayy! Updated!'})

        # Verify the update
        response = self.app.get('/get')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json[0]['message'], new_message)

    def test_delete(self):
        # First, post a message
        self.app.post('/post', json={'message': 'Message to delete'})
        
        # Delete the message
        response = self.app.delete('/delete')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {'response': 'Yayy! Message deleted!'})

        # Verify the deletion
        response = self.app.get('/get')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, [])

if __name__ == '__main__':
    unittest.main()