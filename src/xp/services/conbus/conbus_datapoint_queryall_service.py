import logging
from typing import Callable, Optional, List, Dict

from twisted.internet.posixbase import PosixReactorBase

from xp.models import ConbusClientConfig, ConbusDatapointResponse
from xp.models.telegram.datapoint_type import DataPointType
from xp.models.telegram.system_function import SystemFunction
from xp.services import TelegramService
from xp.services.conbus.conbus_datapoint_service import ConbusDatapointService


class ConbusDatapointQueryAllService:
    """
    Utility service for querying all datapoints from a module.

    This service orchestrates multiple ConbusDatapointService calls to query
    all available datapoint types sequentially.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        cli_config: ConbusClientConfig,
        reactor: PosixReactorBase,
    ):
        """Initialize the query all service

        Args:
            telegram_service: TelegramService for dependency injection
            cli_config: ConbusClientConfig for connection settings
            reactor: PosixReactorBase for async operations
        """
        self.telegram_service = telegram_service
        self.cli_config = cli_config
        self.reactor = reactor
        self.logger = logging.getLogger(__name__)

    def query_all_datapoints(
        self,
        serial_number: str,
        finish_callback: Callable[[ConbusDatapointResponse], None],
        timeout_seconds: Optional[float] = None,
    ) -> None:
        """
        Query all available datapoints for a given serial number.

        Args:
            serial_number: 10-digit module serial number
            finish_callback: callback function to call when all queries complete
            timeout_seconds: timeout in seconds for each query
        """
        datapoints: List[Dict[str, str]] = []
        has_any_success = False
        last_error = None
        datapoint_types = list(DataPointType)
        current_index = [0]  # Use list to maintain mutable reference in closure

        def query_next_datapoint() -> None:
            """Query the next datapoint in the list"""
            nonlocal has_any_success, last_error

            if current_index[0] >= len(datapoint_types):
                # All datapoints queried, return final response
                if not has_any_success and last_error:
                    response = ConbusDatapointResponse(
                        success=False,
                        serial_number=serial_number,
                        system_function=SystemFunction.READ_DATAPOINT,
                        error=last_error,
                        datapoints=[],
                    )
                else:
                    response = ConbusDatapointResponse(
                        success=True,
                        serial_number=serial_number,
                        system_function=SystemFunction.READ_DATAPOINT,
                        datapoints=datapoints,
                    )
                finish_callback(response)
                return

            datapoint_type = datapoint_types[current_index[0]]
            current_index[0] += 1

            def on_datapoint_response(response: ConbusDatapointResponse) -> None:
                """Handle response from single datapoint query"""
                nonlocal has_any_success, last_error

                if response.success and response.datapoint_telegram:
                    # Extract datapoint name and value
                    datapoint_name = datapoint_type.name
                    datapoint_value = str(response.datapoint_telegram.data_value)
                    datapoints.append({datapoint_name: datapoint_value})
                    has_any_success = True
                elif response.error:
                    last_error = response.error

                # Query next datapoint
                query_next_datapoint()

            # Create new service instance for this query
            service = ConbusDatapointService(
                telegram_service=self.telegram_service,
                cli_config=self.cli_config,
                reactor=self.reactor,
            )

            with service:
                service.query_datapoint(
                    serial_number=serial_number,
                    datapoint_type=datapoint_type,
                    finish_callback=on_datapoint_response,
                    timeout_seconds=timeout_seconds,
                )

        # Start querying
        query_next_datapoint()

    def __enter__(self) -> "ConbusDatapointQueryAllService":
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: object | None,
    ) -> None:
        # Cleanup logic if needed
        pass
