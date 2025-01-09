import logging
import os
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import BOT_TOKEN, CHANNEL_ID

client = WebClient(token=BOT_TOKEN)
logger = logging.getLogger(__name__)

def file_uploader():
    file_name = "./service_monitoring.pdf"
    channel_id = CHANNEL_ID

    try:
        # Call the files.upload method using the WebClient
        # Uploading files requires the `files:write` scope
        client.files_upload_v2(
            channel=channel_id,
            initial_comment="Today's Service Reporting",
            file=file_name,
        )

    except SlackApiError as e:
        logger.error("Error uploading file: {}".format(e))