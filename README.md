# Task Description
Please write web frontend in Python which presents user with an input form and accepts IPv4 address. The project should then check in the backend if the given IPv4 address is valid or not. If it is not correct, it should display that to the user so. If the IPv4 address is correct, the code should perform reverse Whois using this API - "https://api.threatminer.org/v2/host.php?q=<PLACE_IP_ADDRESS_HERE>&rt=1". You can check the documentation here - https://www.threatminer.org/api.php. The web UI should then display the received result in tabular format. If there is no result for given IP, it should print out appropriate message for the user.

The above result should also be stored with timestamp in Elasticsearch. Every time a user enters the IP address, it should be looked in Elasticsearch for pre-existing result for that IP. If the result exists in Elasticsearch and is not more than 48 hours old, that result should be displayed to user immediately.

# Requirements
Python 3.x

Step 1:
pip install -r requirements.txt

Step 2:
python manager.py runserver

Step 3:
Open http://127.0.0.1:8000/ in browser