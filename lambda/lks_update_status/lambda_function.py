import os
import json
import pymysql
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALLOWED_STATUS = ["PENDING", "ACCEPT", "REJECT"]

conn = None

def get_connection():
    global conn
    if conn is None or not conn.open:
        conn = pymysql.connect(
            host=os.environ["DB_HOST"],
            port=int(os.environ["DB_PORT"]),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            db=os.environ["DB_NAME"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )
    return conn

def lambda_handler(event, context):
    approval_id = event.get("approvalId")
    status = event.get("status")

    if not approval_id:
        raise ValueError("approvalId is required")

    if status not in ALLOWED_STATUS:
        raise ValueError("Invalid status")

    connection = get_connection()

    with connection.cursor() as cursor:
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
            "SELECT id FROM approvals WHERE id = %s",
            (approval_id,)
        )

        if not cursor.fetchone():
            raise ValueError("Approval not found")

        cursor.execute(
            "UPDATE approvals SET status = %s WHERE id = %s",
            (status, approval_id)
        )

        cursor.execute(
            "UPDATE approvals SET task_token = null WHERE id = %s",
            (approval_id)
        )

        connection.commit()

    return {
        "approvalId": approval_id,
        "status": status
    }
