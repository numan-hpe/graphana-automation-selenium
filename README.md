## Automated Service Monitoring Reports
A simple selenium script that generates service monitoring reports from Graphana and complies it into a PDF, optionally auto-publishing it to a Slack channel of your choice.
### Steps to get this working:
- Clone the repo and install dependencies: `pip install -r requirements.txt`
- Update `config.py`
  - Set USER_EMAIL with your HPE email ID
  - [Optional] Set PIN to your SSO PIN if you want auto PIN entry (Disabled by default)
  - [Optional] Set BOT_TOKEN and CHANNEL_ID with your Slack Bot Token/Channel ID for auto-publishing the report to the Slack channel (disabled by default)
- Run `python3 graphana_selenium.py`
- Wait for the initial login to complete where you have to select the browser certificate and enter your SSO PIN.
- Grab a coffee / take a break / focus on some other work 🙂
- The Service Monitoring report will be generated and saved in the repo dir 
