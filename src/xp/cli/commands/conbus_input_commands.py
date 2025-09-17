"""Conbus client operations CLI commands."""

import click
import json

from ...services.conbus_client_send_service import (
    ConbusClientSendService,
    ConbusClientSendError,
)
from ...services.input_service import XPInputService, XPInputError
from ...models.action_type import ActionType
from ..utils.decorators import (
    connection_command,
    handle_service_errors,
)
from ..utils.error_handlers import CLIErrorHandler
from .conbus import conbus


@conbus.command("input")
@click.argument("serial_number", type=click.STRING)
@click.argument("input_number_or_status", type=click.Choice(["status", "0", "1", "2", "3", "4", "5", "6", "7", "8"]))
@click.argument("on_or_off", type=click.Choice(["on", "off"]), default="on")
@connection_command()
@handle_service_errors(ConbusClientSendError)
def xp_input(
    serial_number: str, input_number_or_status: str, on_or_off: str
):
    """Send input command to XP module or query status.

    Examples:

    \b
        xp conbus input 0011223344 0 on     # Toggle input 0
        xp conbus input 0011223344 1 off    # Toggle input 1
        xp conbus input 0011223344 status   # Query status
    """
    service = ConbusClientSendService()
    input_service = XPInputService()

    try:
        with service:
            if input_number_or_status.lower() == "status":
                # Send status query using custom telegram method
                response = service.send_custom_telegram(
                    serial_number,
                    input_service.STATUS_FUNCTION,  # "02"
                    input_service.STATUS_DATAPOINT,  # "12"
                )

                # Add XP24-specific data to response
                response_data = response.to_dict()
                response_data["xp24_operation"] = "status_query"
                response_data["telegram_type"] = "xp_input"

                # Parse status from response if available
                if response.success and response.received_telegrams:
                    try:
                        status = input_service.parse_status_response(
                            response.received_telegrams[0]
                        )
                        response_data["input_status"] = status
                    except XPInputError:
                        # Status parsing failed, keep raw response
                        pass

                click.echo(json.dumps(response_data, indent=2))

            else:
                # Parse input number and send action
                try:
                    input_number = int(input_number_or_status)
                    input_service.validate_input_number(input_number)
                except (ValueError, XPInputError):
                    error_msg = f"Invalid input number: {input_number_or_status}"
                    error_response = {
                        "success": False,
                        "error": error_msg,
                        "valid_inputs": [0, 1, 2, 3],
                        "xp24_operation": "action_command",
                    }
                    click.echo(json.dumps(error_response, indent=2))
                    raise SystemExit(1)

                # Send action telegram using custom telegram method
                # Format: F27D{input:02d}AA (Function 27, input number, PRESS action)
                action_type = ActionType.RELEASE.value
                if on_or_off.lower() == "on":
                    action_type = ActionType.PRESS.value

                data_point_code = f"{input_number:02d}{action_type}"
                response = service.send_custom_telegram(
                    serial_number,
                    input_service.ACTION_FUNCTION,  # "27"
                    data_point_code,  # "00AA", "01AA", etc.
                )

                # Add XP24-specific data to response
                response_data = response.to_dict()
                response_data["xp24_operation"] = "action_command"
                response_data["input_number"] = input_number
                response_data["action_type"] = "press"
                response_data["telegram_type"] = "xp_action"
                click.echo(json.dumps(response_data, indent=2))

    except XPInputError as e:
        error_response = {
            "success": False,
            "error": str(e),
            "xp24_operation": "validation_error",
        }
        click.echo(json.dumps(error_response, indent=2))
        raise SystemExit(1)

    except ConbusClientSendError as e:
        CLIErrorHandler.handle_service_error(e, "XP Input", {
            "serial_number": serial_number,
            "input_number_or_status": input_number_or_status,
            "on_or_off": on_or_off,
        })
