import os
import boto3
import pymysql

sns = boto3.client("sns")

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
    task_token = event.get("taskToken")
    approvalId = event.get("approvalId")
    approvalType = event.get("type")
    subject = event.get("subject")
    description = event.get("description")

    if not all([task_token, approvalId, approvalType, subject, description]):
        raise ValueError("Missing required approval data")

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
            UPDATE approvals
            SET task_token = %s
            WHERE id = %s
            """,
            (task_token, approvalId)
        )

    approve_url = (
        f"https://70w9yixy67.execute-api.us-east-1.amazonaws.com/Prod"
        f"/approval/signal/{approvalId}?decision=ACCEPT"
    )
    reject_url = (
        f"https://70w9yixy67.execute-api.us-east-1.amazonaws.com/Prod"
        f"/approval/signal/{approvalId}?decision=REJECT"
    )

    message = f"""
Approval Required

Subject: {subject}
Type: {approvalType}

Description:
{description}

Approve:
{approve_url}

Reject:
{reject_url}
""".strip()

    sns.publish(
        TopicArn=os.environ["TOPIC_ARN"],
        Subject="Approval Required",
        Message=message,
        MessageAttributes={
            "Type": {
                "DataType": "String",
                "StringValue": approvalType
            }
        }
    )

    return {
        "approvalId": approvalId
    }
