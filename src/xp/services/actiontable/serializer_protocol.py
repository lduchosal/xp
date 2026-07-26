# Copyright (c) 2025 ldvchosal
"""Protocol for action table serializers."""

from typing import Protocol, TypeVar

from xp.models.telegram.system_function import SystemFunction

T = TypeVar("T")


class ActionTableSerializerProtocol(Protocol[T]):
    """Protocol defining the interface for action table serializers.

    All action table serializers (ActionTableSerializer, Xp20MsActionTableSerializer,
    Xp24MsActionTableSerializer, Xp33MsActionTableSerializer) implement this protocol,
    parametrized by the action table model type they handle.
    """

    @staticmethod
    def download_type() -> SystemFunction:
        """Get the download system function type.

        Returns:
            The download system function: DOWNLOAD_MSACTIONTABLE or DOWNLOAD_ACTIONTABLE

        """
        ...

    @staticmethod
    def from_encoded_string(encoded_data: str) -> T:
        """Deserialize encoded telegram data to action table model.

        Args:
            encoded_data: Encoded string from telegram (A-P nibble encoding).

        Returns:
            Deserialized action table model.

        """
        ...

    @staticmethod
    def to_encoded_string(action_table: T) -> str:
        """Serialize action table model to encoded telegram format.

        Args:
            action_table: Action table model to serialize.

        Returns:
            Encoded string for telegram transmission.

        """
        ...

    @staticmethod
    def from_short_string(action_strings: list[str]) -> T:
        """Deserialize human-readable short format to action table model.

        Args:
            action_strings: List of short format strings.

        Returns:
            Deserialized action table model.

        """
        ...

    @staticmethod
    def to_short_string(action_table: T) -> list[str]:
        """Serialize action table model to human-readable short format.

        Args:
            action_table: Action table model to serialize.

        Returns:
            List of human-readable short format strings.

        """
        ...
