# Google Cal to Email Reminder
-checks events in a calendar
-sends an email to a specific address --here a google group with the content of the event etc.
# Todo

- implement subcalendar selection. X
	- test out that it works. X
- modify the formatting to the email. X
- implement crontab job on by computer. X
- test out with some fake events. X

# What's needed?
- install googleAPI following this doc: xxxxxxURLxxxxx
	- make sure to also enable the google calendar API

#Crontabjob
`10 8 * * * cd /Users/boutonnetbpa/Dropbox/mailerdeamon && python lacgmailer.py`
