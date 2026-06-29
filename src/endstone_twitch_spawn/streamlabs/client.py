import streamlabsio
import endstone
from .events import StreamlabsEventHandler

class StreamlabsClient:
    def __init__(self, logger: endstone.Logger, token: str, streamlabs_event_handler: StreamlabsEventHandler):
        self._token = token
        self._logger = logger
        self._client = streamlabsio.connect(token=self._token)
        self._streamlabs_event_handler = streamlabs_event_handler

    def start(self):
        try:
            self._client.__enter__()
            self._logger.info("Successfully connected to Streamlabs Socket API")
        except Exception as e:
            self._logger.error(f"Failed to start Streamlabs client: {e}")

    def stop(self):
        try:
            self._client.__exit__(None, None, None)
        except Exception as e:
            self._logger.error(f"Failed to stop Streamlabs client: {e}")

    