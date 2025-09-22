# HomeKit cache service

Conson module are expensive and slow to query :
- ConbusOutputService get_output_state

is called frequently and costy.

## cli integration

```shell
xp cache set <serial_number> <telegram> <event>
xp cache get <serial_number> <event>
xp cache received <event>
```

## Caching 

output states are cached 
use cachetools library
create a caching service 
get_output_state

api is 
```python
class ConsonModule {
    serial_number: str,
    module_type_code: int,
    link_number: int
}

def get(self, serial_number:str, event: str) -> str {
    cachekey : module.serial_number
    tags : event
    
    if in cache:
        return cached data

    data = ConsonOutputService.get_output_state
    cache data
    return data
}
```

## Expiration

```python
def received_event(self, event:str) -> None {
    remove from cache where event match a tag
}

def received_update(self, serial_number: str, event:str, data:str) -> None {
    update cache with fresh data
    keep tags
}

```

## persistance

persist cache in file


