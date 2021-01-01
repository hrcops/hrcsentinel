import smtplib

# starting to hack together from here: https://www.reddit.com/r/Python/comments/8gb88e/free_alternatives_to_twilio_for_sending_text/


def send(message):
        # Replace the number with your own, or consider using an argument\dict for multiple people.
	to_number = '207-504-4862@vtext.com')
	auth=('**email**', '**password**')

	# Establish a secure session with gmail's outgoing SMTP server using your gmail account
	server=smtplib.SMTP("smtp.gmail.com", 587)
	server.starttls()
	server.login(auth[0], auth[1])

	# Send text message through SMS gateway of destination number
	server.sendmail(auth[0], to_number, message)
