import os
import time
from flask import Flask, jsonify, request
import boto3
import uuid

app = Flask(__name__)

# Set region name and dummy credentials
REGION_NAME = 'us-east-1'
AWS_ACCESS_KEY_ID = 'fake_access_key'
AWS_SECRET_ACCESS_KEY = 'fake_secret_key'
os.environ['S3_ENDPOINT_URL'] = 'http://localstack:4566'
os.environ['DYNAMODB_ENDPOINT_URL'] = 'http://localstack:4566'

# Initialize boto3 clients for DynamoDB and S3 with the specified region and dummy credentials
dynamodb = boto3.resource(
    'dynamodb',
    region_name=REGION_NAME,
    endpoint_url=os.environ['DYNAMODB_ENDPOINT_URL'],
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

s3 = boto3.client(
    's3',
    region_name=REGION_NAME,
    endpoint_url=os.environ['S3_ENDPOINT_URL'],
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Define your DynamoDB table and S3 bucket
TABLE_NAME = 'messages'
BUCKET_NAME = 'message-bucket'

def init_localstack():
    time.sleep(5)  # wait for LocalStack to be ready
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
        print(f"Error initializing LocalStack: {e}")

    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
    except s3.exceptions.BucketAlreadyOwnedByYou:
        pass

init_localstack()

@app.route('/')
def home():
    return "Hello World!"

@app.route('/get', methods=['GET'])
def get_message():
    table = dynamodb.Table(TABLE_NAME)
    response = table.scan()
    return jsonify(response['Items'])

@app.route('/get/<id>', methods=['GET'])
def get_message_by_id(id):
    table = dynamodb.Table(TABLE_NAME)
    response = table.get_item(Key={'id': id})
    if 'Item' in response:
        return jsonify(response['Item'])
    else:
        return jsonify({'error': 'Message not found'}), 404

@app.route('/post', methods=['POST'])
def post_message():
    data = request.get_json()
    message = data.get('message', 'Say Hi to Isha!')
    id = str(uuid.uuid4())
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item={'id': id, 'message': message})
    s3.put_object(Bucket=BUCKET_NAME, Key=f'{id}.txt', Body=message)
    return jsonify({'response': f'You sent: {message}', 'id': id})

@app.route('/put/<id>', methods=['PUT'])
def put_message(id):
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Oops! No message has been provided!'}), 400

    table = dynamodb.Table(TABLE_NAME)
    try:
        # Check if the item exists before updating
        response = table.get_item(Key={'id': id})
        if 'Item' not in response:
            return jsonify({'error': 'Message not found'}), 404
        
        # Attempt to update the item in DynamoDB
        table.update_item(
            Key={'id': id},
            UpdateExpression='SET message = :val',
            ExpressionAttributeValues={':val': data['message']}
        )
        
        # Attempt to update the object in S3
        s3.put_object(Bucket=BUCKET_NAME, Key=f'{id}.txt', Body=data['message'])
        return jsonify({'response': 'Yayy! Updated!'})
    
    except dynamodb.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            return jsonify({'error': 'Message not found'}), 404
        else:
            return jsonify({'error': 'An error occurred'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete/<id>', methods=['DELETE'])
def delete_message(id):
    table = dynamodb.Table(TABLE_NAME)
    try:
        table.delete_item(Key={'id': id})
        s3.delete_object(Bucket=BUCKET_NAME, Key=f'{id}.txt')
        return jsonify({'response': 'Yayy! Message deleted!'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')