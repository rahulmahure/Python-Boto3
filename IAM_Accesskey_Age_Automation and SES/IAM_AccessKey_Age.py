import boto3
from datetime import date, datetime, timedelta,timezone
from datetime import date
import csv
import os
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart

def accesskey_fun(writer):
	
	empty_dict_IAM = {}

	client = boto3.client('iam')

	iam_users_var = client.list_users()
	for i in iam_users_var['Users']:
		all_iam_users = i['UserName']

		acc_key_response_var = client.list_access_keys(UserName=all_iam_users)
		for j in acc_key_response_var['AccessKeyMetadata']:
			User_Crated_Date = j['CreateDate']
			accesskey = j['AccessKeyId']
	

			Todays_date = datetime.now(timezone.utc)

			age_access_key = (Todays_date - User_Crated_Date).days

			if (age_access_key >= 10):
				empty_dict_IAM['Username'] = all_iam_users
				empty_dict_IAM['CreateDate'] = User_Crated_Date
				empty_dict_IAM['age_of_key'] = age_access_key
				
				writer.writerow(empty_dict_IAM)
				print (empty_dict_IAM)

def send_email_report(file_name):
	SENDER = "rahulmahure3@gmail.com"
	RECIPIENT = "rahulmahure3@gmail.com"
	SUBJECT = "Accesskey 10 Age Data"
	ATTACHMENT = file_name
	BODY_HTML = """\
	<html>
	<head></head>
	<body>
	<h3>Hi All</h3>
	<p>Please see the attached file for a list of Accesskey those are created 10days ago.</p>
	</body>
	</html>
	"""
	CHARSET = "utf-8"
	client = boto3.client('ses')
	msg = MIMEMultipart('mixed')
	msg['Subject'] = SUBJECT 
	msg['From'] = SENDER 
	msg['To'] = RECIPIENT
	
	msg_body = MIMEMultipart('alternative')
	htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
	msg_body.attach(htmlpart)
	att = MIMEApplication(open(ATTACHMENT, 'rb').read())
	att.add_header('Content-Disposition','attachment',filename=os.path.basename(ATTACHMENT))
	msg.attach(msg_body)
	msg.attach(att)
	try:
	    response = client.send_raw_email(
	        Source=SENDER,
	        Destinations=[
	            RECIPIENT
	        ],
	        RawMessage={
	            'Data':msg.as_string(),
	        }
	    ) 
	except ClientError as e:
	    print(e.response['Error']['Message'])
	else:
	    print("Email sent! Message ID:"),
	    print(response['MessageId'])

def lambda_handler(event, context):
	fieldnames = ["Username","CreateDate","age_of_key"]
	file_name = "/tmp/empty_dict_IAM.csv"
	with open (file_name,"w",newline='') as csv_file:
		writer = csv.DictWriter(csv_file,fieldnames=fieldnames)
		writer.writeheader()
		accesskey_fun(writer)
	send_email_report(file_name)