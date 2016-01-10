# coding: utf8
#!/usr/bin/python3

SCOPES = [ 'https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/gmail.send' ]
WHERE_DOES_THE_MAIL_GO_TO = "lacg@googlegroups.com"

import httplib2
import os

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import datetime
from email.mime.text import MIMEText
import base64

try:
	import argparse
	flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
	flags = None

def get_credentials():
	"""Gets valid user credentials from storage.

	If nothing has been stored, or if the stored credentials are invalid,
	the OAuth2 flow is completed to obtain the new credentials.

	Returns:
		Credentials, the obtained credential.
	"""
	credential_path = os.path.join('.','credentials.json')
	store = oauth2client.file.Storage(credential_path)
	credentials = store.get()
	if not credentials or credentials.invalid:
		flow = client.flow_from_clientsecrets('client_secret.json',SCOPES)
		flow.user_agent = 'pythonMailer'
		credentials = tools.run_flow(flow,store,flags)
		print 'Storing credentials to ' + credential_path
	return credentials

def SendMessage(service, user_id, message):
	"""Send an email message.

	Args:
		service: Authorized Gmail API service instance.
		user_id: User's email address. The special value "me"
		can be used to indicate the authenticated user.
		message: Message to be sent.

	Returns:
		Sent Message.
	"""
	message = (service.users().messages().send(userId=user_id, body=message)
						 .execute())
	#print 'Message Id: %s' % message['id']
	return message

def CreateMessage(sender, to, subject, message_text):
	"""Create a message for an email.

	Args:
		sender: Email address of the sender.
		to: Email address of the receiver.
		subject: The subject of the email message.
		message_text: The text of the email message.

	Returns:
		An object containing a base64 encoded email object.
	"""
	message = MIMEText(message_text)
	message['to'] = to
	message['from'] = sender
	message['subject'] = subject
	return {'raw': base64.b64encode(message.as_string())}

def send_email(serviceMail,tomorrow,start,place,title,abstract):
	t = datetime.datetime.strptime((start.split('+'))[0],"%Y-%m-%dT%H:%M:%S") #split off tz modifier: 2015-12-24T06:30:00>>>+01:00<<<
	time = t.strftime('%H:%M')
	date = t.strftime('%A %d %B')
	subject_tag = date + ':' #
	body_tag = 'Here is what is happening next week:\n\n'
	dotorbang = '.'
	if date == tomorrow.strftime('%A %d %B'):
		subject_tag = 'Reminder: tomorrow'
		body_tag = "Tomorrow in the LACG meeting:\n\n"
		dotorbang = '!'
	if place != '':
		place = 'Location: ' + place
	#if abstract != '':
		#abstract = "Abstract:\n\n" + abstract

	sender = "Your friendly LACG mailbot"
	recipient = WHERE_DOES_THE_MAIL_GO_TO
	subject = subject_tag + ' ' + title
	body = "Dear LACG members,\n\n" + body_tag + "Speaker: " + title + "\n\n" + place + '\n\nTime: ' + time + "\n\n" + abstract #+ "\n\nBest,\nBastien, Min, Yifei, and Cesko"

	gmail_message = CreateMessage(sender,recipient,subject,body.encode('utf8'))
	return SendMessage(serviceMail,'me',gmail_message)

def main():
	credentials = get_credentials()
	http = credentials.authorize(httplib2.Http())
	serviceCal = discovery.build('calendar', 'v3', http=http)

	now = datetime.datetime.today()
	today = datetime.date(now.year,now.month,now.day) #rounded down, i.e. 00:00 in the morning!
	tomorrow_beg = today + datetime.timedelta(days=1)

	# if it's not a Friday, check events for tomorrow only
	lim_beg = tomorrow_beg.isoformat() + 'T00:00:00.00000Z'
	lim_end = tomorrow_beg.isoformat() + 'T23:59:59.99999Z' # this is not really correct because it's assuming we're UTC
	if now.weekday() == 4: # Friday
		lim_end = tomorrow_beg + datetime.timedelta(days=6) #not just tomorrow, but the whole week!
		lim_end = lim_end.isoformat() + 'T23:59:59.99999Z'

	eventsResult = serviceCal.events().list(
		calendarId='ms91c3puq1l5fckj1rc4dn4clk@group.calendar.google.com', timeMin=lim_beg, timeMax=lim_end, singleEvents=True,
		orderBy='startTime').execute()
	events = eventsResult.get('items', [])

	if events:
		serviceMail = discovery.build('gmail', 'v1', http=http)
		for event in events:
			start = event['start'].get('dateTime', event['start'].get('date'))
			place = ''
			abstract = ''
			try:
				place = event['location']
			except KeyError:
				pass
			try:
				abstract = event['description']
			except KeyError:
				pass
			send_email(serviceMail,tomorrow_beg,start,place,event['summary'],abstract)

if __name__ == '__main__':
	main()
