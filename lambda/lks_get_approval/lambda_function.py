import os
import pymysql
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        # Database connection
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
            # Auto-create table if not exists
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
            
            conn.commit()

            cursor.execute("SELECT id, subject, description, type, status FROM approvals")
            approval = cursor.fetchall()

        return {
            'statusCode': 200,
            'body': json.dumps(approval, default=str)
        }

    except pymysql.MySQLError as e:
        logger.error("Database error: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps(f'Database error: {str(e)}')
        }
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
    finally:
        if 'conn' in locals():
            conn.close()