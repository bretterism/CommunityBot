import base64
import boto3
import logging
import json
import requests

# BOT_IDS: Each key is the group ID, and the value is the encrypted Bot ID.
# The encryption/decryption of the IDs is done through AWS KMS.
BOT_IDS = {
	# Test Bot Group
	'50989408': 'AQICAHjA5rkU31IWZL+nKbVhtwdHzJE55TKGkGxqXO5Ye2y89QGLUsApcGZRHvyl9JTrE4uuAAAAeDB2BgkqhkiG9w0BBwagaTBnAgEAMGIGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMENCTz719L2JhvZ5TAgEQgDWxW8jToLXsKTkmaiLtA5r1C8pbisIK4voWJ64VUZSPPPLkpsyj2OzqolgMUA1yTK4/0Qawxw==',
    # Community Group
    '35209810': 'AQICAHgIXsveqob+/veYRjxX0trbPNZty+moGi8wiV8AY6gFvQFRtmH3p1xTXqoV9tcLEYA5AAAAeDB2BgkqhkiG9w0BBwagaTBnAgEAMGIGCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMEgtzk1mJw17rKu9iAgEQgDVJfLP9rgDL164C5biae5Nkakmt59N+Q4Rzt//nP62v2NUGCmm8q2FEbHYCSMYg9Ayi8icP6w=='
}

# The API Url
API_URL = 'https://api.groupme.com/v3/bots/post'

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def post_message(bot_id, message):
	body = {
		'bot_id': bot_id,
		'text': message
	}

	return requests.post(API_URL, json=body)

def get_bot_id(group):
    """Get the bot ID for a group."""
    blob = base64.b64decode(BOT_IDS[group])
    client = boto3.client('kms')
    bot_id = client.decrypt(CiphertextBlob=blob)['Plaintext']
    return bot_id.decode('ascii')

def lambda_handler(event, context):
    # TODO implement
    bot_id = get_bot_id(event['Bot_ID'])

    msg = event['Message']
    post_message(bot_id, msg)

    return {
        'statusCode': 200
    }