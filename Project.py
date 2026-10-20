import os
import time
import boto3
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# =====================================
# CONFIGURATION
# =====================================
WATCH_FOLDER = "/home/ec2-user/ProjectFolder"
BUCKET_NAME = "abcnewaws"  # S3 bucket names are global, use your own unique name
SNS_TOPIC_ARN = "arn:aws:sns:ap-south-1:<ACCOUNT_ID>:ProjectNotification"

# =====================================
# LOGGING
# =====================================
logging.basicConfig(
    filename="/home/ec2-user/ProjectLogs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# =====================================
# AWS CLIENTS
# Credentials come from the IAM role attached to the EC2 instance
# =====================================
s3 = boto3.client("s3", region_name="ap-south-1")
sns = boto3.client("sns", region_name="ap-south-1")


# =====================================
# SNS NOTIFICATION
# =====================================
def send_notification(file_name):
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Backup Successful",
            Message=f"""
Cloud Backup Completed Successfully

File Name : {file_name}

Bucket : {BUCKET_NAME}

Time : {time.ctime()}
"""
        )
        print("SNS Email Sent Successfully")
        logging.info(f"SNS notification sent for {file_name}")
    except Exception as e:
        print("SNS Error:", e)
        logging.error(f"SNS Error: {e}")


# =====================================
# UPLOAD TO S3
# =====================================
def upload_file(file_path):
    try:
        file_name = os.path.basename(file_path)
        print(f"Uploading {file_name}...")
        s3.upload_file(file_path, BUCKET_NAME, file_name)
        print(f"{file_name} uploaded successfully.")
        logging.info(f"{file_name} uploaded successfully.")
        send_notification(file_name)
    except Exception as e:
        print("Upload Error:", e)
        logging.error(f"Upload failed: {e}")


# =====================================
# WATCHDOG
# =====================================
class BackupHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        print(f"New File Detected : {event.src_path}")
        logging.info(f"New file detected : {event.src_path}")
        time.sleep(2)  # give the file time to finish writing
        upload_file(event.src_path)


# =====================================
# MAIN
# =====================================
if __name__ == "__main__":
    print("=" * 50)
    print("Cloud Backup System Started")
    print("=" * 50)
    print(f"Monitoring Folder: {WATCH_FOLDER}")
    logging.info("Cloud Backup System Started")

    event_handler = BackupHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_FOLDER, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Cloud Backup System Stopped")
    observer.join()
