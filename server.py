import os
from flask import Flask, jsonify, request
import boto3

app = Flask(__name__)

# Set region name and dummy credentials
REGION_NAME = 'us-east-1'
AWS_ACCESS_KEY_ID = 'fake_access_key'
AWS_SECRET_ACCESS_KEY = 'fake_secret_key'

# Initialize boto3 clients for DynamoDB and S3 with the specified region and dummy credentials
dynamodb = boto3.resource(
    'dynamodb',
    region_name=REGION_NAME,
    endpoint_url='http://localhost:4566',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

s3 = boto3.client(
    's3',
    region_name=REGION_NAME,
    endpoint_url='http://localhost:4566',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Define your DynamoDB table and S3 bucket
TABLE_NAME = 'messages'
BUCKET_NAME = 'message-bucket'

# Ensure the table and bucket are created
def init_localstack():
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

@app.route('/post', methods=['POST'])
def post_message():
    data = request.get_json()
    message = data.get('message', 'Say Hi to Isha!')
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item={'id': '1', 'message': message})
    s3.put_object(Bucket=BUCKET_NAME, Key='message.txt', Body=message)
    return jsonify({'response': f'You sent: {message}'})

@app.route('/put', methods=['PUT'])
def put_message():
    data = request.get_json()
    if 'message' in data:
        message = data['message']
        table = dynamodb.Table(TABLE_NAME)
        table.update_item(
            Key={'id': '1'},
            UpdateExpression='SET message = :val',
            ExpressionAttributeValues={':val': message}
        )
        s3.put_object(Bucket=BUCKET_NAME, Key='message.txt', Body=message)
        return jsonify({'response': 'Yayy! Updated!'})
    else:
        return jsonify({'error': 'Oops! No message has been provided!'}), 400

@app.route('/delete', methods=['DELETE'])
def delete_message():
    table = dynamodb.Table(TABLE_NAME)
    table.delete_item(Key={'id': '1'})
    s3.delete_object(Bucket=BUCKET_NAME, Key='message.txt')
    return jsonify({'response': 'Yayy! Message deleted!'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')