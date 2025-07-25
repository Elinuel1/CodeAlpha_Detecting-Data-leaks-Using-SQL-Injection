import json
import boto3
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('SecureUsers')  # I'll create this in Terraform

# Dummy AES key for now (must be 32 bytes for AES-256)
KEY = b'ThisIsASecretKey1234567890123456'
CAPABILITY_CODE = "ALLOW_SQL_OP"

def encrypt_data(plaintext):
    cipher = AES.new(KEY, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return {"iv": iv, "ciphertext": ct}

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        username = body.get('username')
        password = body.get('password')
        code = body.get('capability_code')

        if code != CAPABILITY_CODE:
            return {
                'statusCode': 403,
                'body': json.dumps({'error': 'Unauthorized access'})
            }

        encrypted_pw = encrypt_data(password)

        table.put_item(Item={
            'username': username,
            'password': encrypted_pw['ciphertext'],
            'iv': encrypted_pw['iv']
        })

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'User added securely!'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
