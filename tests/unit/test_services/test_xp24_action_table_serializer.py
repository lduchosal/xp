# Copyright (c) 2025 ldvchosal
"""Unit tests for XP24 Action Table Serializer."""

import pytest

from xp.models.actiontable.msactiontable_xp24 import InputAction, Xp24MsActionTable
from xp.models.telegram.input_action_type import InputActionType
from xp.models.telegram.timeparam_type import TimeParam
from xp.services.actiontable.msactiontable_xp24_serializer import (
    Xp24MsActionTableSerializer,
)
from xp.utils.serialization import de_nibbles


class TestXp24MsActionTableSerializer:
    """Test cases for Xp24MsActionTableSerializer."""

    @pytest.fixture
    def sample_action_table(self) -> Xp24MsActionTable:
        """Create sample action table for testing.

        Returns:
            Sample action table for testing.

        """
        return Xp24MsActionTable(
            input1_action=InputAction(
                type=InputActionType.TOGGLE, param=TimeParam.NONE
            ),
            input2_action=InputAction(type=InputActionType.ON, param=TimeParam.T5SEC),
            input3_action=InputAction(
                type=InputActionType.LEVELSET, param=TimeParam.T5SEC
            ),
            input4_action=InputAction(
                type=InputActionType.SCENESET, param=TimeParam.T5SEC
            ),
            mutex12=True,
            mutex34=False,
            mutual_deadtime=Xp24MsActionTable.MS500,
            curtain12=False,
            curtain34=True,
        )

    @pytest.fixture
    def sample_telegrams(self) -> list[str]:
        """Create sample telegrams for testing.

        Returns:
            Sample telegrams for testing.

        """
        return [
            "<R0020044989F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFA>",
            "<R0020044966F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFB>",
            "<R0020044986F17DAAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFP>",
            "<R0020041824F17DAAAAAAAAAAABACAEAIBACAEAIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFP>",
            "<R0020044964F17DAAAAABAGADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFD>",
        ]

    def test_from_telegrams_invalid_hex_data(self) -> None:
        """Test decoding an encoded action table with default TOGGLE actions."""
        # Data portion of the sample telegram from device 0020044989
        valid_telegram = (
            "ADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )

        msactiontable = Xp24MsActionTableSerializer.from_encoded_string(valid_telegram)
        assert msactiontable.input1_action.type == InputActionType.TOGGLE
        assert msactiontable.input2_action.type == InputActionType.TOGGLE
        assert msactiontable.input3_action.type == InputActionType.TOGGLE
        assert msactiontable.input4_action.type == InputActionType.TOGGLE

        assert msactiontable.input1_action.param == TimeParam.NONE
        assert msactiontable.input2_action.param == TimeParam.NONE
        assert msactiontable.input3_action.param == TimeParam.NONE
        assert msactiontable.input4_action.param == TimeParam.NONE

        assert not msactiontable.curtain12
        assert not msactiontable.curtain34
        assert not msactiontable.mutex12
        assert not msactiontable.mutex34

    def test_from_telegrams_from_data(self) -> None:
        """Test encode/decode round-trip preserves the encoded string."""
        # Data portion of the sample telegram from device 0020044989
        valid_msactiontable = (
            "ADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )

        msactiontable = Xp24MsActionTableSerializer.from_encoded_string(
            valid_msactiontable
        )
        msactiontable_data = Xp24MsActionTableSerializer.to_encoded_string(
            msactiontable
        )
        assert valid_msactiontable == msactiontable_data

    def test_from_telegrams_invalid_hex_data2(self) -> None:
        """Test decoding an encoded action table with an ON action and T15SEC."""
        # Data portion of the sample telegram from device 0020044964
        valid_telegram = (
            "ABAGADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
        )

        msactiontable = Xp24MsActionTableSerializer.from_encoded_string(valid_telegram)
        assert msactiontable.input1_action.type == InputActionType.ON
        assert msactiontable.input2_action.type == InputActionType.TOGGLE
        assert msactiontable.input3_action.type == InputActionType.TOGGLE
        assert msactiontable.input4_action.type == InputActionType.TOGGLE

        assert msactiontable.input1_action.param == TimeParam.T15SEC
        assert msactiontable.input2_action.param == TimeParam.NONE
        assert msactiontable.input3_action.param == TimeParam.NONE
        assert msactiontable.input4_action.param == TimeParam.NONE

        assert not msactiontable.curtain12
        assert not msactiontable.curtain34
        assert not msactiontable.mutex12
        assert not msactiontable.mutex34

    def test_from_telegrams_de_nibble_0(self) -> None:
        """Test de_nibbles decodes 'AA' to a single zero byte."""
        nibble = "AA"

        result = de_nibbles(nibble)
        assert bytearray([0]) == result

    def test_from_telegrams_de_nibble_1(self) -> None:
        """Test de_nibbles decodes 'AB' to a single byte of value 1."""
        nibble = "AB"

        result = de_nibbles(nibble)
        assert bytearray([1]) == result

    def test_from_telegrams_de_nibble_01(self) -> None:
        """Test de_nibbles decodes 'AAAB' to bytes 0 and 1."""
        nibble = "AAAB"

        result = de_nibbles(nibble)
        assert bytearray([0, 1]) == result

    def test_from_telegrams_de_nibble_big(self) -> None:
        """Test de_nibbles decodes a full action table payload."""
        nibble = "AAAAADAAADAAADAAADAAAAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

        result = de_nibbles(nibble)
        assert (
            bytearray(
                [
                    0,
                    0,
                    3,
                    0,
                    3,
                    0,
                    3,
                    0,
                    3,
                    0,
                    0,
                    0,
                    12,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                    0,
                ]
            )
            == result
        )
