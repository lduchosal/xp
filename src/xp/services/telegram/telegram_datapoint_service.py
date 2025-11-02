"""Service for processing Telegram protocol datapoint values."""


class TelegramDatapointService:
    """Service for processing Telegram protocol datapoint values.

    Provides methods to parse and extract values from different types of
    Telegram datapoints including autoreport status, light level outputs,
    and link number values.
    """

    def get_autoreport_status(self, data_value: str) -> bool:
        """Get the autoreport status value.

        Args:
            data_value: The raw autoreport status data value (PP or AA).

        Returns:
            The autoreport status: Enable (True) or disable (False).
        """
        status_value = True if data_value == "PP" else False
        return status_value

    def get_autoreport_status_data_value(self, status_value: bool) -> str:
        """Get the autoreport status data_value.

        Args:
            status_value: Enable (True) or disable (False).

        Returns:
            data_value: The raw autoreport status data value (PP or AA).
        """
        data_value = "PP" if status_value else "AA"
        return data_value

    def get_lightlevel(self, data_value: str, output_number: int) -> int:
        """Extract the light level for a specific output number.

        Parses comma-separated output data in the format "output:level[%]"
        and returns the level for the requested output number.

        Args:
            data_value: Comma-separated string of output:level pairs
                       (e.g., "1:50[%],2:75[%]").
            output_number: The output number to get the level for.

        Returns:
            The light level as an integer (0 if output not found).
        """
        level = 0
        for output_data in data_value.split(","):
            if ":" in output_data:
                output_str, level_str = output_data.split(":")
                if int(output_str) == output_number:
                    level_str = level_str.replace("[%]", "")
                    level = int(level_str)
                    break
        return level

    def get_linknumber(self, data_value: str) -> int:
        """Parse and return the link number value.

        Args:
            data_value: The raw link number data value as a string.

        Returns:
            The link number as an integer.
        """
        link_number_value = int(data_value)
        return link_number_value

    def get_modulenumber(self, data_value: str) -> int:
        """Parse and return the module number value.

        Args:
            data_value: The raw module number data value as a string.

        Returns:
            The module number as an integer.
        """
        module_number_value = int(data_value)
        return module_number_value
