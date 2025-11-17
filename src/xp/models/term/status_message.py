"""Status message models for terminal UI."""

from textual.message import Message


class StatusMessageChanged(Message):
    """Message posted when status message changes."""

    def __init__(self, message: str) -> None:
        """Initialize the message.

        Args:
            message: The status message to display.
        """
        super().__init__()
        self.message = message
