# Refactoring: implement IoC

For each service in the list below:

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
   - Mark service as complete below

## Service list


[ ] ActionTableService
[ ] MsActionTableService
[ ] ConbusAutoreportService
[ ] ConbusBlinkService
[ ] ConbusCustomService
[ ] ConbusDatapointService
[ ] ConbusDiscoverService
[ ] ConbusLightlevelService
[ ] ConbusLinknumberService
[ ] ConbusOutputService
[ ] ConbusRawService
[ ] ConbusReceiveService
[ ] ConbusScanService
[ ] ConbusService
[ ] HomeKitCacheService
[ ] HomekitModuleService
[ ] HomekitService
[ ] LogFileService
[ ] ModuleTypeService
[ ] ReverseProxyService
[ ] BaseServerService
[ ] CP20ServerService
[ ] ServerService
[ ] XP130ServerService
[ ] XP20ServerService
[ ] XP230ServerService
[ ] XP24ServerService
[ ] XP33ServerService
[ ] TelegramBlinkService
[ ] TelegramChecksumService
[ ] DeviceInfo
[ ] TelegramDiscoverService
[ ] LinkNumberService
[ ] TelegramOutputService
[ ] TelegramService
[ ] VersionService
