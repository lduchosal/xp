"""Connection state management module."""

from enum import Enum

from xp.utils.state_machine import StateMachine


class ConnectionState(str, Enum):
    """Connection state enumeration.

    Attributes:
        DISCONNECTING: Disconnecting to server.
        DISCONNECTED: Not connected to server.
        CONNECTING: Connection in progress.
        CONNECTED: Successfully connected.
        FAILED: Connection failed.
    """

    DISCONNECTING = "DISCONNECTING"
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    FAILED = "FAILED"

    @staticmethod
    def create_state_machine() -> StateMachine:
        """Create and configure state machine for connection management.

        Returns:
            Configured StateMachine with connection state transitions.
        """
        sm = StateMachine(ConnectionState.DISCONNECTED)

        # Define valid transitions
        sm.define_transition(
            "connect", {ConnectionState.DISCONNECTED, ConnectionState.FAILED}
        )
        sm.define_transition(
            "disconnect", {ConnectionState.CONNECTED, ConnectionState.CONNECTING}
        )
        sm.define_transition(
            "connecting", {ConnectionState.DISCONNECTED, ConnectionState.FAILED}
        )
        sm.define_transition("connected", {ConnectionState.CONNECTING})
        sm.define_transition(
            "disconnecting", {ConnectionState.CONNECTED, ConnectionState.CONNECTING}
        )
        sm.define_transition("disconnected", {ConnectionState.DISCONNECTING})
        sm.define_transition(
            "failed",
            {
                ConnectionState.CONNECTING,
                ConnectionState.CONNECTED,
                ConnectionState.DISCONNECTING,
            },
        )

        return sm
