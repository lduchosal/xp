
from xp.services.homekit.homekit_service import HomeKitService

from xp.utils.dependencies import ServiceContainer

if __name__ == "__main__":

    container = ServiceContainer()
    homekit_service = container.get_container().resolve(HomeKitService)
    homekit_service.run()
