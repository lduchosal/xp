"""Conbus Scan Service for TCP communication with Conbus servers.

This service implements a TCP client that scan a Conbus servers and sends
various types of telegrams including discovery, version, and sensor data requests.
"""

import logging
from typing import List

from .conbus_service import ConbusService
from ..models import (
    ConbusResponse,
    ConbusRequest,
)
from ..models.system_function import SystemFunction
from ..services.telegram_service import TelegramService


class ConbusScanError(Exception):
    """Raised when Conbus client send operations fail"""

    pass


class ConbusScanService:
    """
    TCP client service for sending telegrams to Conbus servers.

    Manages TCP socket connections, handles telegram generation and transmission,
    and processes server responses.
    """

    def __init__(self, config_path: str = "cli.yml"):
        """Initialize the Conbus client send service"""

        # Service dependencies
        self.telegram_service = TelegramService()
        self.conbus_service = ConbusService()

        # Set up logging
        self.logger = logging.getLogger(__name__)

    def scan_module(
        self, serial_number: str, system_function: SystemFunction, progress_callback=None
    ) -> List[ConbusResponse]:
        """Scan all functions and datapoints for a module with live output"""
        results = []
        total_combinations = 256 * 256  # 65536 combinations
        count = 0

        for datapoint_hex in range(256):
            data = f"{datapoint_hex:02X}"
            count += 1

            try:
                response = self.conbus_service.send_telegram(
                    serial_number, system_function, data
                )
                results.append(response)

                # Call progress callback with live results
                if progress_callback:
                    progress_callback(response, count, total_combinations)

                # Small delay to prevent overwhelming the server
                import time

                time.sleep(0.001)  # 1ms delay

            except Exception as e:
                # Create error response for failed scan attempt
                error_response = ConbusResponse(
                    success=False,
                    request=ConbusRequest(
                        serial_number=serial_number,
                        function_code=function_code,
                        data=data,
                    ),
                    error=f"Scan failed for F{function_code}D{data}: {e}",
                )
                results.append(error_response)

                # Call progress callback with error response
                if progress_callback:
                    progress_callback(error_response, count, total_combinations)

        return results

    def scan_module_background(self, serial_number: str, progress_callback=None):
        """Scan module in background with immediate output via callback"""
        import threading

        def background_scan():
            return self.scan_module(serial_number, progress_callback)

        # Start background thread
        scan_thread = threading.Thread(target=background_scan, daemon=True)
        scan_thread.start()

        return scan_thread

