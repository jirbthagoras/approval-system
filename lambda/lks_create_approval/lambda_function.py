import os
import pymysql
import json
import boto3

sf = boto3.client("stepfunctions")

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        
        required_fields = ['subject', 'description', 'type']
        for field in required_fields:
            if field not in body:
                return {
                    'statusCode': 400,
                    'body': json.dumps(f'Missing required field: {field}')
                }

        approval_type = ['BUY', 'SALE', 'AUDIT']
        if body['type'] not in approval_type:
            return {
                    'statusCode': 400,
                    'body': json.dumps(f'Invalid type: {body["type"]}')
                }

        conn = pymysql.connect(
            host=os.environ['DB_HOST'],
            port=int(os.environ['DB_PORT']),
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            db=os.environ['DB_NAME'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS approvals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    subject VARCHAR(255) NOT NULL,
                    description VARCHAR(255) NOT NULL,
                    type VARCHAR(255),
                    status VARCHAR(255),
                    task_token TEXT
                );
            ''')

            cursor.execute('''
                INSERT INTO approvals (
                    subject, description, type, status
                ) VALUES (%s, %s, %s, %s)
            ''', (
                body['subject'],
                body['description'],
                body.get('type'),
                "PENDING",
            ))
            conn.commit()
            new_id = cursor.lastrowid

            cursor.execute('SELECT * FROM approvals WHERE id = %s', (new_id,))
            approval = cursor.fetchone()

            sf.start_execution(
                stateMachineArn=os.environ["STATE_MACHINE_ARN"],
                input=json.dumps({
                    "approvalId": approval["id"],
                    "type": approval["type"],
                    "subject": approval["subject"],
                    "description": approval["description"]
                })
            )


        return {
            'statusCode': 201,
            'body': json.dumps(approval, default=str)
        }

    except pymysql.MySQLError as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Database error: {str(e)}')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
    finally:
        if 'conn' in locals():
            conn.close()
