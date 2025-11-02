"""Tests for DeviceServiceFactory."""

import pytest

from xp.services.actiontable.msactiontable_serializer import MsActionTableSerializer
from xp.services.actiontable.msactiontable_xp20_serializer import (
    Xp20MsActionTableSerializer,
)
from xp.services.actiontable.msactiontable_xp24_serializer import (
    Xp24MsActionTableSerializer,
)
from xp.services.actiontable.msactiontable_xp33_serializer import (
    Xp33MsActionTableSerializer,
)
from xp.services.server.cp20_server_service import CP20ServerService
from xp.services.server.device_service_factory import DeviceServiceFactory
from xp.services.server.xp20_server_service import XP20ServerService
from xp.services.server.xp24_server_service import XP24ServerService
from xp.services.server.xp33_server_service import XP33ServerService
from xp.services.server.xp130_server_service import XP130ServerService
from xp.services.server.xp230_server_service import XP230ServerService


@pytest.fixture
def factory():
    """Create a device service factory with mock serializers."""
    xp20_serializer = Xp20MsActionTableSerializer()
    xp24_serializer = Xp24MsActionTableSerializer()
    xp33_serializer = Xp33MsActionTableSerializer()
    ms_serializer = MsActionTableSerializer()

    return DeviceServiceFactory(
        xp20ms_serializer=xp20_serializer,
        xp24ms_serializer=xp24_serializer,
        xp33ms_serializer=xp33_serializer,
        ms_serializer=ms_serializer,
    )


class TestDeviceServiceFactoryInit:
    """Test DeviceServiceFactory initialization."""

    def test_init(self, factory):
        """Test factory initialization with serializers."""
        assert factory.xp20ms_serializer is not None
        assert factory.xp24ms_serializer is not None
        assert factory.xp33ms_serializer is not None
        assert factory.ms_serializer is not None


class TestDeviceServiceFactoryCreateDevice:
    """Test DeviceServiceFactory.create_device()."""

    def test_create_xp20(self, factory):
        """Test creating XP20 device."""
        device = factory.create_device("XP20", "12345")

        assert isinstance(device, XP20ServerService)
        assert device.serial_number == "12345"
        assert device.device_type == "XP20"

    def test_create_xp24(self, factory):
        """Test creating XP24 device."""
        device = factory.create_device("XP24", "23456")

        assert isinstance(device, XP24ServerService)
        assert device.serial_number == "23456"
        assert device.device_type == "XP24"

    def test_create_xp33(self, factory):
        """Test creating XP33 device."""
        device = factory.create_device("XP33", "33333")

        assert isinstance(device, XP33ServerService)
        assert device.serial_number == "33333"
        assert device.variant == "XP33"

    def test_create_xp33lr(self, factory):
        """Test creating XP33LR device."""
        device = factory.create_device("XP33LR", "33334")

        assert isinstance(device, XP33ServerService)
        assert device.serial_number == "33334"
        assert device.variant == "XP33LR"

    def test_create_xp33led(self, factory):
        """Test creating XP33LED device."""
        device = factory.create_device("XP33LED", "33335")

        assert isinstance(device, XP33ServerService)
        assert device.serial_number == "33335"
        assert device.variant == "XP33LED"

    def test_create_cp20(self, factory):
        """Test creating CP20 device."""
        device = factory.create_device("CP20", "44444")

        assert isinstance(device, CP20ServerService)
        assert device.serial_number == "44444"
        assert device.device_type == "CP20"

    def test_create_xp130(self, factory):
        """Test creating XP130 device."""
        device = factory.create_device("XP130", "55555")

        assert isinstance(device, XP130ServerService)
        assert device.serial_number == "55555"
        assert device.device_type == "XP130"

    def test_create_xp230(self, factory):
        """Test creating XP230 device."""
        device = factory.create_device("XP230", "66666")

        assert isinstance(device, XP230ServerService)
        assert device.serial_number == "66666"
        assert device.device_type == "XP230"

    def test_create_unknown_device(self, factory):
        """Test creating unknown device type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            factory.create_device("UNKNOWN", "99999")

        assert "Unknown device type 'UNKNOWN'" in str(exc_info.value)
        assert "99999" in str(exc_info.value)


class TestDeviceServiceFactorySerializerInjection:
    """Test that serializers are properly injected."""

    def test_xp20_has_serializer(self, factory):
        """Test XP20 device receives correct serializer."""
        device = factory.create_device("XP20", "12345")

        assert device.msactiontable_serializer is not None
        assert isinstance(device.msactiontable_serializer, Xp20MsActionTableSerializer)

    def test_xp24_has_serializer(self, factory):
        """Test XP24 device receives correct serializer."""
        device = factory.create_device("XP24", "23456")

        assert device.msactiontable_serializer is not None
        assert isinstance(device.msactiontable_serializer, Xp24MsActionTableSerializer)

    def test_xp33_has_serializer(self, factory):
        """Test XP33 device receives correct serializer."""
        device = factory.create_device("XP33", "33333")

        assert device.msactiontable_serializer is not None
        assert isinstance(device.msactiontable_serializer, Xp33MsActionTableSerializer)
