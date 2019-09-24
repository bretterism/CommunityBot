import base64
import boto3
import datetime
import gspread
import json
import logging
from oauth2client.service_account import ServiceAccountCredentials

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_client_secret(filename):
    """Get the client secret from encrypted file. Returns decrypted json object"""
    with open(filename) as file:
        json_file = json.load(file)

    cyphertext = json_file['CiphertextBlob']
    blob = base64.b64decode(cyphertext)
    client = boto3.client('kms')
    secret = client.decrypt(CiphertextBlob=blob)['Plaintext']
    s = secret.decode('ascii')
    return json.loads(s)

def connect(filename):
	# use creds to create a client to interact with the Google Drive API
	scope = ['https://spreadsheets.google.com/feeds',
	         'https://www.googleapis.com/auth/drive']

	keyfile_dict = get_client_secret(filename)
	creds = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict=keyfile_dict, scopes=scope)
	client = gspread.authorize(creds)

	return client

def get_dinner_titles(workbook):
	"""gets the list of available dinners from the workbook by worksheet titles"""

	worksheets = workbook.worksheets()
	worksheet_titles = [i.title for i in worksheets]
	# Exclude system titles
	worksheet_titles.remove('History')
	worksheet_titles.remove('Settings')

	return worksheet_titles

def get_next_dinner_title(workbook):
	"""gets the title of the next dinner"""

	# Check for override in the settings tab
	settings_worksheet = workbook.worksheet('Settings')
	override_cell = settings_worksheet.find('Override')
	override_value = settings_worksheet.cell(override_cell.row, 2).value

	next_dinner = override_value

	# Checking dinner dates in the History tab
	worksheet_titles = get_dinner_titles(workbook)
	if override_value not in worksheet_titles:
		# Get next week's dinner template by selecting the oldest date from the history table
		history_worksheet = workbook.worksheet('History')
		history_values = history_worksheet.get_all_values()

		oldest_date = datetime.datetime.now()
		next_dinner = ''
		for h in history_values:
			dinner_date = datetime.datetime.strptime(h[1], '%m/%d/%Y %H:%M:%S')
			print(h[0], dinner_date)
			if dinner_date <= oldest_date:
				next_dinner = h[0]
				oldest_date = dinner_date
	else:
		# Clear the override so next week will be back on the regular rotation
		settings_worksheet.update_cell(override_cell.row, override_cell.col+1, '')

	return next_dinner

def get_next_dinner(workbook):
	next_dinner_title = get_next_dinner_title(workbook)
	print(next_dinner_title)
	return workbook.worksheet(next_dinner_title)

def get_dinner_items(worksheet):
	"""gets the list of items from the worksheet dinner template"""
	dinner_items = worksheet.col_values(1)
	dinner_items = [d.strip(' ') for d in dinner_items]

	return dinner_items

def reset_spreadsheet(worksheet, theme_location, fooditem_range):
	"""clears last week's items from the spreadsheet"""

	# Clear dinner theme
	worksheet.update_acell(theme_location, '')

	# Clear dinner items
	range_of_cells = worksheet.range(fooditem_range)
	for cell in range_of_cells:
	    cell.value = ''
	worksheet.update_cells(range_of_cells)

def insert_new_dinner(dinner_worksheet, template_worksheet, theme_location, fooditem_range):

	dinner_items = get_dinner_items(template_worksheet)
	dinner_theme = template_worksheet.title

	# Adding new dinner theme
	dinner_worksheet.update_acell(theme_location, dinner_theme)

	# Adding new dinner items
	fooditem_range_start = fooditem_range.split(':')[0]
	fooditem_cell = dinner_worksheet.acell(fooditem_range_start)
	for idx, item in enumerate(dinner_items):
		update_row = fooditem_cell.row + idx
		update_col = fooditem_cell.col

		dinner_worksheet.update_cell(update_row, update_col, item)

def set_history_date(workbook, dinner_theme):
	history_worksheet = workbook.worksheet('History')
	theme_cell = history_worksheet.find(dinner_theme)

	datetime_now = datetime.datetime.now().strftime('%m/%d/%Y %H:%M:%S')
	history_worksheet.update_cell(theme_cell.row, theme_cell.col+1, datetime_now)

	print(datetime_now)

def notify_users(bot_id, msg):
	lam = boto3.client('lambda')

	payload = {}
	payload['Bot_ID'] = bot_id
	payload['Message'] = msg
	try:
		response = lam.invoke(FunctionName='NotifyUsers',
							  InvocationType='RequestResponse',
							  Payload=json.dumps(payload))
	except Exception as e:
		print(e)
		raise e


def lambda_handler(event, context):

	logger.info(event)

	# Variables
	theme_location = 'B1'
	fooditem_range = 'A4:B50'

	# Obtain client connection
	client = connect('client_secret_encrypted.json')

	# Gather workbooks/worksheets
	workbook_templates_name = event['Templates_Workbook']
	workbook_dinner_name = event['Dinner_Workbook']
	worksheet_dinner_name = event['Dinner_Worksheet']

	workbook_template = client.open(workbook_templates_name)
	workbook_dinner = client.open(workbook_dinner_name)
	dinner_worksheet = workbook_dinner.worksheet(worksheet_dinner_name)

	dinner_template_worksheet = get_next_dinner(workbook_template)
	dinner_theme = dinner_template_worksheet.title

	# Clear out last week's dinner
	reset_spreadsheet(dinner_worksheet, theme_location, fooditem_range)

	# Insert new dinner
	insert_new_dinner(dinner_worksheet, dinner_template_worksheet, theme_location, fooditem_range)

	# Set the timestamp for the new dinner in the history sheet
	set_history_date(workbook_template, dinner_theme)

	# Notify Users the new spreadsheet is up
	spreadsheet_url = 'https://docs.google.com/spreadsheets/d/{}/edit?usp=sharing'.format(workbook_dinner.id)
	msg = 'Community Bot here *Bleep* *Bloop*\nThe new spreadsheet is up! Next week''s theme is {}.\nPlease sign-up for a few items to share!\n{}'.format(dinner_theme, spreadsheet_url)

	notify_users(event['Bot_ID'], msg)
