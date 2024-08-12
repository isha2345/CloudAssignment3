import unittest
import json
import boto3
from server import app, dynamodb, TABLE_NAME, BUCKET_NAME, s3, init_localstack

class FlaskTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.s3 = boto3.client('s3', endpoint_url='http://localstack:4566')
        cls.s3.create_bucket(Bucket=BUCKET_NAME)
        init_localstack()

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Initialize DynamoDB table
        self.table = dynamodb.Table(TABLE_NAME)
        self.table.put_item(Item={'id': '1', 'message': 'Initial message'})

        # Initialize S3 bucket with an initial object
        s3.put_object(Bucket=BUCKET_NAME, Key='1.txt', Body='Initial message')

    def tearDown(self):
        # Empty the S3 bucket
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' in response:
            for obj in response['Contents']:
                s3.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])

        # Clean up DynamoDB table
        self.table.delete_item(Key={'id': '1'})

    def test_home(self):
        result = self.app.get('/')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data.decode('utf-8'), "Hello World!")

    def test_get_message(self):
        result = self.app.get('/get?id=1')
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['message'], 'Initial message')

        # Verify DynamoDB state
        dynamodb_response = self.table.get_item(Key={'id': '1'})
        self.assertEqual(dynamodb_response['Item']['message'], 'Initial message')

        # Verify S3 state
        s3_response = s3.get_object(Bucket=BUCKET_NAME, Key='1.txt')
        self.assertEqual(s3_response['Body'].read().decode('utf-8'), 'Initial message')

    def test_get_no_results(self):
        result = self.app.get('/get?id=nonexistent')
        self.assertEqual(result.status_code, 404)
        data = json.loads(result.data)
        self.assertEqual(data['error'], 'No item found with the given ID')

    def test_get_no_parameters(self):
        result = self.app.get('/get')
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['message'], 'Initial message')

    def test_get_incorrect_parameters(self):
        result = self.app.get('/get?incorrect=1')
        self.assertEqual(result.status_code, 400)
        data = json.loads(result.data)
        self.assertEqual(data['error'], 'Invalid parameters')

    def test_post_message(self):
        result = self.app.post('/post', json={'id': '2', 'message': 'Hello from test!'})
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['response'], 'You sent: Hello from test!')

        # Verify the message in DynamoDB
        response = self.table.get_item(Key={'id': '2'})
        self.assertEqual(response['Item']['message'], 'Hello from test!')

        # Verify the message in S3
        s3_response = s3.get_object(Bucket=BUCKET_NAME, Key='2.txt')
        self.assertEqual(s3_response['Body'].read().decode('utf-8'), 'Hello from test!')

    def test_post_duplicate_message(self):
        self.app.post('/post', json={'id': '2', 'message': 'Hello from test!'})
        result = self.app.post('/post', json={'id': '2', 'message': 'Hello again!'})
        self.assertEqual(result.status_code, 400)
        data = json.loads(result.data)
        self.assertEqual(data['error'], 'Duplicate ID')

    def test_put_message(self):
        result = self.app.put('/put', json={'id': '1', 'message': 'Updated message from test!'})
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['response'], 'Yayy! Updated!')

        # Verify the updated message in DynamoDB
        response = self.table.get_item(Key={'id': '1'})
        self.assertEqual(response['Item']['message'], 'Updated message from test!')

        # Verify the updated message in S3
        s3_response = s3.get_object(Bucket=BUCKET_NAME, Key='1.txt')
        self.assertEqual(s3_response['Body'].read().decode('utf-8'), 'Updated message from test!')

    def test_put_message_no_valid_target(self):
        result = self.app.put('/put', json={'id': 'nonexistent', 'message': 'This should not work'})
        self.assertEqual(result.status_code, 404)
        data = json.loads(result.data)
        self.assertEqual(data['error'], 'No item found with the given ID')

    def test_put_message_no_message(self):
        result = self.app.put('/put', json={'id': '1'})
        self.assertEqual(result.status_code, 400)
        data = json.loads(result.data)
        self.assertEqual(data['error'], 'Invalid input')

    def test_delete_message(self):
        result = self.app.delete('/delete?id=1')
        self.assertEqual(result.status_code, 200)
        data = json.loads(result.data)
        self.assertEqual(data['response'], 'Yayy! Message deleted!')

        # Verify the message is deleted in DynamoDB
        response = self.table.get_item(Key={'id': '1'})
        self.assertNotIn('Item', response)

        # Verify the object is deleted in S3
        with self.assertRaises(s3.exceptions.NoSuchKey):
            s3.get_object(Bucket=BUCKET_NAME, Key='1.txt')

    def test_delete_message_no_id(self):
        result = self.app.delete('/delete')
        self.assertEqual(result.status_code, 400)
        data = json.loads(result.data)
        self.assertEqual(data['error'], 'ID parameter is required')

    def test_delete_message_no_valid_target(self):
        result = self.app.delete('/delete?id=nonexistent')
        self.assertEqual(result.status_code, 404)
        data = json.loads(result.data)
        self.assertEqual(data['error'], 'No item found with the given ID')

if __name__ == '__main__':
    unittest.main()