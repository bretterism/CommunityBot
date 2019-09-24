#!/bin/bash

# Variables
LAMBDA_FILENAMES="notify-users.py"
LAMBDA_FUNCTION="NotifyUsers"
DEPENDENCIES="requests"

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