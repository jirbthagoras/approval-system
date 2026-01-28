import json
import os
import logging
import pymysql
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sf = boto3.client("stepfunctions")

ALLOWED_DECISIONS = ["ACCEPT", "REJECT"]

def get_db():
    return pymysql.connect(
        host=os.environ['DB_HOST'],
        port=int(os.environ['DB_PORT']),
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        db=os.environ['DB_NAME'],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def lambda_handler(event, context):
    try:
        approval_id = event["pathParameters"]["id"]

        params = event.get("queryStringParameters") or {}
        decision = params.get("decision")

        if decision not in ALLOWED_DECISIONS:
            return response(400, "Invalid decision")

        conn = get_db()
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

            cursor.execute(
                """
                SELECT task_token
                FROM approvals
                WHERE id = %s
                """,
                (approval_id,)
            )
            row = cursor.fetchone()

            if not row or not row["task_token"]:
                return response(410, "Approval already processed or expired")

            task_token = row["task_token"]

            print(task_token)

        sf.send_task_success(
            taskToken=task_token,
            output=json.dumps({
                "approvalId": approval_id,
                "status": decision
            })
        )

        return response(200, {
            "message": f'Approval sent, Status: {decision}'
        })

    except ClientError as e:
        if e.response["Error"]["Code"] in ["TaskTimedOut", "TaskDoesNotExist", "InvalidToken"]:
            logger.error("Invalid or expired task token")
            return response(410, "Task token expired or invalid")
        raise

    except Exception as e:
        logger.exception("Unexpected error")
        return response(500, "Internal server error")

def response(status_code, body):
    return {
        "statusCode": status_code,
        "body": json.dumps(body)
    }
