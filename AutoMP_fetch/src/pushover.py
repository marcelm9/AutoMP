import sys

import requests

from src.job import Job
from src.log import Log


class Pushover:
    def __init__(self, job: Job):
        self._job = job
        self._api_token, self._user_token, self._device = job.get_pushover()

    def perform_check(self):
        Log.info("Starting pushover test")

        success, error_message = self.send("This is the test message")
        if success:
            Log.success("Pushover test successful")
        else:
            Log.error(f"Failed to send notification: {error_message}")
            sys.exit(1)

    def send(self, message: str) -> tuple[bool, str]:
        """Send a pushover notification

        Args:
            title (str): Title of the notification
            message (str): Message of the notification

        Returns:
            bool: True if the notification was sent successfully, False otherwise
            str: Error message if the notification was not successful
        """
        data = {
            "token": self._api_token,
            "user": self._user_token,
            "device": self._device,
            "message": message,
        }
        if self._device is not None:
            data["device"] = self._device
        try:
            response = requests.post(
                url="https://api.pushover.net/1/messages.json",
                data=data,
            )
        except Exception as e:
            return False, str(e)

        if response.status_code != 200:
            return False, ", ".join(response.json()["errors"])

        return True, ""
