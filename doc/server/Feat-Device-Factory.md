# Server Device Factory

## Problem

Current `ServerService._create_device_services()` violates Single Responsibility Principle:
- Long if-elif chain with hardcoded device instantiation
- Direct coupling to all device service classes
- Difficult to test and extend with new device types
- Serializer passing logic mixed with creation logic

## Solution

Implement **Device Factory** pattern with dependency injection:
- Factory encapsulates device creation logic
- Registered in ServiceContainer for DI
- Maps module types to device service constructors
- Handles serializer injection automatically

## Architecture

```
ServerService
    ↓ (depends on)
DeviceServiceFactory
    ↓ (creates)
BaseServerService (XP20, XP24, XP33, CP20, XP130, XP230)
```

## Implementation

### 1. DeviceServiceFactory Class

**Location**: `src/xp/services/server/device_service_factory.py`

**Responsibilities**:
- Register device type → constructor mappings
- Create device instances with correct serializers
- Handle variant-based device types (XP33, XP33LR, XP33LED)

**Interface**:
```python
class DeviceServiceFactory:
    def __init__(
        self,
        xp20ms_serializer: Xp20MsActionTableSerializer,
        xp24ms_serializer: Xp24MsActionTableSerializer,
        xp33ms_serializer: Xp33MsActionTableSerializer,
        ms_serializer: MsActionTableSerializer,
    ):
        """Initialize with all serializers via DI."""

    def create_device(
        self,
        module_type: str,
        serial_number: str,
    ) -> BaseServerService:
        """Create device instance for given module type.

        Args:
            module_type: Module type code (e.g., "XP20", "XP33LR")
            serial_number: Device serial number

        Returns:
            Device service instance

        Raises:
            ValueError: If module_type is unknown
        """
```

### 2. Update ServerService

**Changes**:
- Inject `DeviceServiceFactory` via constructor
- Replace `_create_device_services()` logic with factory calls
- Remove direct device service imports
- Simplify error handling

**Before**:

```python
if module_type == "XP20":
    self.device_services[serial_number] = XP20ServerService(
        serial_number, "XP20", self.msactiontable_serializer_xp20
    )
```

**After**:
```python
self.device_services[serial_number] = self.factory.create_device(
    module_type, serial_number
)
```

### 3. Update ServiceContainer

Register factory in DI container:
```python
self.container.register(
    DeviceServiceFactory,
    factory=lambda: DeviceServiceFactory(
        xp20ms_serializer=self.container.resolve(Xp20MsActionTableSerializer),
        xp24ms_serializer=self.container.resolve(Xp24MsActionTableSerializer),
        xp33ms_serializer=self.container.resolve(Xp33MsActionTableSerializer),
        ms_serializer=self.container.resolve(MsActionTableSerializer),
    ),
    scope=punq.Scope.singleton,
)
```

## Todo List

- [ ] Create `DeviceServiceFactory` class in `src/xp/services/server/device_service_factory.py`
  - [ ] Add constructor accepting all serializers
  - [ ] Implement `create_device()` method with type mapping
  - [ ] Handle variant-based types (XP33/XP33LR/XP33LED)
  - [ ] Add proper error handling for unknown types
  - [ ] Add complete docstrings (Google style)

- [ ] Update `ServerService` class
  - [ ] Add `device_factory: DeviceServiceFactory` to constructor
  - [ ] Refactor `_create_device_services()` to use factory
  - [ ] Remove direct device service imports (keep only base class)
  - [ ] Update error handling to use factory exceptions

- [ ] Update `ServiceContainer`
  - [ ] Register `DeviceServiceFactory` as singleton
  - [ ] Inject all serializers into factory
  - [ ] Update `ServerService` registration to inject factory

- [ ] Add unit tests
  - [ ] Test factory device creation for all types
  - [ ] Test unknown module type handling
  - [ ] Test serializer injection
  - [ ] Test variant handling (XP33 variants)

- [ ] Run quality checks
  - [ ] `pdm lint` - Linting
  - [ ] `pdm typecheck` - Type checking
  - [ ] `pdm test` - All tests pass
  - [ ] `pdm check` - Full quality validation

## Quality Requirements

- **Type Safety**: All methods fully typed (no `Any` types)
- **Documentation**: Complete docstrings for all public methods
- **Error Handling**: Raise `ValueError` for unknown module types
- **Testing**: Minimum 90% coverage for factory class
- **DRY**: No code duplication between factory and services
- **SOLID**: Factory follows Single Responsibility and Open/Closed principles

## Benefits

- **Maintainability**: Single place to add new device types
- **Testability**: Factory can be mocked independently
- **Extensibility**: Easy to add new device types without modifying ServerService
- **Separation of Concerns**: Device creation logic isolated
- **Dependency Injection**: All dependencies properly injected
