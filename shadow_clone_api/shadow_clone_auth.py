"""This module Generates JWT Tokens and mails it to associate recipients daily"""

import os.path, json, dotenv, base64
from datetime import timedelta, date


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from flask import Flask
from flask_jwt_extended import create_access_token
from flask_jwt_extended import JWTManager


app = Flask(__name__)
app.config.from_object("config.DevConfig")
jwt = JWTManager(app)
google_credentials = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


def generate_jwt():
    with app.app_context():
        jwt_token = create_access_token(
            identity="LTUC_USER", expires_delta=timedelta(hours=24)
        )
    return jwt_token


def generate_ws_jwt():
    with app.app_context():
        jwt_token = create_access_token(
            identity="WS_LTUC_USER", expires_delta=timedelta(minutes=20), fresh=True
        )
    return jwt_token


def authenticate_gmail(active_jwt_token):

    creds = None

    if "GOOGLE_TOKEN" in os.environ:
        google_token = json.loads(os.getenv("GOOGLE_TOKEN"))
        creds = Credentials.from_authorized_user_info(google_token, SCOPES)

    # If there are no (valid) credentials available, let the user log in (in order to get valid ones).
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            config = json.loads(os.environ["GOOGLE_CREDENTIALS"])

            flow = InstalledAppFlow.from_client_config(
                config,
                SCOPES,
            )
            creds = flow.run_local_server(port=5555)

        os.environ["GOOGLE_TOKEN"] = creds.to_json()
        dotenv.set_key(".env", "GOOGLE_TOKEN", creds.to_json())

    try:

        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)

        my_email = os.getenv("MY_EMAIL")
        dev_mail = os.getenv("DEV_EMAIL")
        mailing_list = os.getenv("MAIL_LIST")

        date_ = date.today()
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Automated email] - {date_} active JWT"
        msg["From"] = f"{my_email}"
        msg["To"] = f"{mailing_list}"
        encoded_jwt = base64.b64encode(active_jwt_token.encode()).decode()
        msgPlain = f"Good Morning!\nToday's ENCODED JWT token:\n{encoded_jwt}\nAuthorization Header would look like this:\nAuthorization: Bearer <DECODED JWT TOKEN> \n\n Refer to https://www.base64decode.org in order to decode yor token (use UTF-8 character set) \n\nFor help or to unsubscribe, send me an email on {dev_mail}"
        msgHtml = f'<h1>Good Morning!</h1><br><h2>Today\'s ENCODED JWT token:</h2><br> <div style = "border-color: rgb(190,190,190) ;border-style: solid; background-color: rgb(200,200,200); color: rgb(250,250,250)"> <code> { encoded_jwt } </code> </div> <br><br>Authorization Header would look like this:<br><br> <br><code style= "border-color: rgb(230,230,230) ;border-style: solid;">  Authorization: Bearer <i> DECODED JWT TOKEN </i>  </code><br> <br><br>  Refer to <a href="https://www.base64decode.org"> Base64 </a> in order to decode yor token (use UTF-8 character set)  <br><br> For help or to unsubscribe, send me an email on {dev_mail}'
        msg.attach(MIMEText(msgPlain, "plain"))
        msg.attach(MIMEText(msgHtml, "html"))
        raw = base64.urlsafe_b64encode(msg.as_bytes())
        raw = raw.decode()
        body = {"raw": raw}

        message1 = body
        message = service.users().messages().send(userId="me", body=message1).execute()
        print("Message Id: %s" % message["id"])

    except HttpError as error:
        # TODO Handle errors from gmail API
        print(f"An error occurred: {error}")


def tasks():
    generated_jwt = generate_jwt()
    authenticate_gmail(generated_jwt)