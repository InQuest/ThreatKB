import json
import requests

class SlackHelper():

    @staticmethod
    def send_slack_message(web_hook, user, channel, message):
        """Send a slack message

        @param web_hook: slack web hook
        @param user: slack user
        @param channel: slack channel to post to
        @param message: the message to send
        @return: True on success, false otherwise
        @author: danny
        """

        payload = {"text": message, "username": user, "channel": channel}

        req = requests.post(web_hook, json.dumps(payload), headers={'content-type': 'application/json'})
        return True
