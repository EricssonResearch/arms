from flask import Flask
import os
import sys

app = Flask(__name__)

@app.route('/alarms')
def alarms():

	with open(os.getcwd() + '/alarmSample.txt', 'r') as f:
		lines = f.readlines()
		f.close()
	for line in lines:
		if "Link Failure" in line:
			return line[line.find("RiPort") + 7:line.find("RiPort") + 8]

	return "no alarm"


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)
