#!/bin/bash

# Variables
LAMBDA_FILENAMES="update-spreadsheet.py client_secret_encrypted.json"
LAMBDA_FUNCTION="UpdateSpreadsheet"
DEPENDENCIES="gspread oauth2client"

# Internal variables
ZIP_FILENAME="$LAMBDA_FUNCTION.zip"
ZIP_FILEURL="fileb://$ZIP_FILENAME"

# Creating zip package
rm $ZIP_FILENAME
zip $ZIP_FILENAME $LAMBDA_FILENAMES

# Adding dependencies to package
mkdir libs
pip install -t libs $DEPENDENCIES
cd libs
zip -r ../$ZIP_FILENAME *
cd ..
rm -rf libs

# Deploying to AWS
aws lambda update-function-code --function-name $LAMBDA_FUNCTION --zip-file $ZIP_FILEURL