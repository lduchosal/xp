class TelegramDatapointService:

    def get_autoreport_status(self, data_value: str) -> str:
        return data_value

    def get_lightlevel_level(self, data_value: str, output_number: int) -> int:
        level = 0
        for output_data in data_value.split(
            ","
        ):
            if ":" in output_data:
                output_str, level_str = output_data.split(":")
                if int(output_str) == output_number:
                    level_str = level_str.replace("[%]", "")
                    level = int(level_str)
                    break
        return level

    def get_linknumber_value(self, data_value: str) -> int:
        link_number_value = int(data_value)
        return link_number_value
