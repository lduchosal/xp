# Refactoring: implement IoC

You are given an agent number agentX
For each service in the list dev/service_refactor_agentX.txt

## Service Refactoring Steps

1. **Update Service Constructor**
   - Remove all `Optional[]` type hints from service dependencies
   - Remove all default `= None` values from service parameters
   - Remove `or ServiceName(...)` instantiation patterns
   - Remove `config_path` parameter if unused elsewhere
   - Direct assignment: `self.service = service`

2. **Update CLI Commands**
   - Add `@click.pass_context` decorator
   - Add `ctx: Context` parameter
   - Get service from container: `ctx.obj.get("container").get_container().resolve(ServiceName)`

3. **Update Dependencies Container**
   - Register service in `dependencies.py`
   - Use factory pattern for complex dependencies
   - Set scope to `punq.Scope.singleton`

4. **Fix Tests**
   - Update test fixtures to use container or manual DI
   - Pass all required dependencies explicitly

5. **Validate**
   - Run `./publish.sh --quality` until all checks pass
   - Remove the service from dev/service_refactor.txt

## Example Pattern

**Before:**

```python
def __init__(
        self,
        config_path: str = "cli.yml",
        conbus_protocol: Optional[ConbusProtocol] = None,
):
    self.telegram_protocol = conbus_protocol or ConbusProtocol(config_path)
```

**After:**

```python
def __init__(
        self,
        conbus_protocol: ConbusProtocol,
        datapoint_service: ConbusDatapointService,
):
    self.telegram_protocol = conbus_protocol
    self.datapoint_service = datapoint_service
```

**CLI Before:**
```python
def command():
    service = ServiceName()
```

**CLI After:**
```python
@click.pass_context
def command(ctx: Context):
    service = ctx.obj.get("container").get_container().resolve(ServiceName)
```
