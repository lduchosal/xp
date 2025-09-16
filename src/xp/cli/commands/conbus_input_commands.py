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
@click.argument("serial_number")
@click.argument("input_number_or_status")
@click.argument("on_or_off", type=click.Choice(["on", "off"]), default="on")
@connection_command()
@handle_service_errors(ConbusClientSendError)
def xp_input(
    serial_number: str, input_number_or_status: str, on_or_off: str, json_output: bool
):
    """
    Send input command to XP module or query status.

    Examples:\n
        xp conbus input 0020044964 0 ON    # Toggle input 0\n
        xp conbus input 0020044964 1 OFF   # Toggle input 1
        xp conbus input 0020044964 2 ON    # Toggle input 2
        xp conbus input 0020044964 3 ON    # Toggle input 3
        xp conbus input 0020044964 status  # Query input status
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

                if json_output:
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
                    if response.success:
                        # Format output like conbus examples
                        if response.sent_telegram:
                            timestamp = response.timestamp.strftime("%H:%M:%S,%f")[:-3]
                            click.echo(f"{timestamp} [TX] {response.sent_telegram}")

                        # Show received telegrams and parse status
                        for received in response.received_telegrams:
                            timestamp = response.timestamp.strftime("%H:%M:%S,%f")[:-3]
                            click.echo(f"{timestamp} [RX] {received}")

                            # Parse and display status in human-readable format
                            try:
                                status = input_service.parse_status_response(received)
                                status_summary = input_service.format_status_summary(
                                    status
                                )
                                click.echo(f"\n{status_summary}")
                            except XPInputError:
                                # Status parsing failed, skip formatting
                                pass

                        if not response.received_telegrams:
                            click.echo("No response received")
                    else:
                        click.echo(f"Error: {response.error}")

            else:
                # Parse input number and send action
                try:
                    input_number = int(input_number_or_status)
                    input_service.validate_input_number(input_number)
                except (ValueError, XPInputError):
                    error_msg = f"Invalid input number: {input_number_or_status}"
                    if json_output:
                        error_response = {
                            "success": False,
                            "error": error_msg,
                            "valid_inputs": [0, 1, 2, 3],
                            "xp24_operation": "action_command",
                        }
                        click.echo(json.dumps(error_response, indent=2))
                        raise SystemExit(1)
                    else:
                        click.echo(f"Error: {error_msg}", err=True)
                        click.echo("Valid inputs: 0, 1, 2, 3 or 'status'")
                        raise click.ClickException("Invalid input number")

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

                if json_output:
                    # Add XP24-specific data to response
                    response_data = response.to_dict()
                    response_data["xp24_operation"] = "action_command"
                    response_data["input_number"] = input_number
                    response_data["action_type"] = "press"
                    response_data["telegram_type"] = "xp24_action"
                    click.echo(json.dumps(response_data, indent=2))
                else:
                    if response.success:
                        # Format output like conbus examples
                        if response.sent_telegram:
                            timestamp = response.timestamp.strftime("%H:%M:%S,%f")[:-3]
                            click.echo(f"{timestamp} [TX] {response.sent_telegram}")

                        # Show received telegrams
                        for received in response.received_telegrams:
                            timestamp = response.timestamp.strftime("%H:%M:%S,%f")[:-3]
                            click.echo(f"{timestamp} [RX] {received}")

                        if not response.received_telegrams:
                            click.echo("No response received")
                        else:
                            click.echo(f"XP24 action sent: Press input {input_number}")
                    else:
                        click.echo(f"Error: {response.error}")

    except XPInputError as e:
        if json_output:
            error_response = {
                "success": False,
                "error": str(e),
                "xp24_operation": "validation_error",
            }
            click.echo(json.dumps(error_response, indent=2))
            raise SystemExit(1)
        else:
            click.echo(f"XP24 Error: {e}", err=True)
            raise click.ClickException(str(e))

    except ConbusClientSendError as e:
        CLIErrorHandler.handle_service_error(
            e,
            json_output,
            "XP Input",
            {
                "serial_number": serial_number,
                "input_number_or_status": input_number_or_status,
                "on_or_off": on_or_off,
            },
        )
