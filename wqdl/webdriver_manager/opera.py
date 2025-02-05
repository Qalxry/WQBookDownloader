import os
from typing import Optional

from wqdl.webdriver_manager.core.download_manager import DownloadManager
from wqdl.webdriver_manager.core.driver_cache import DriverCacheManager
from wqdl.webdriver_manager.core.manager import DriverManager
from wqdl.webdriver_manager.core.os_manager import OperationSystemManager
from wqdl.webdriver_manager.drivers.opera import OperaDriver


class OperaDriverManager(DriverManager):
    def __init__(
            self,
            version: Optional[str] = None,
            name: str = "operadriver",
            url: str = "https://github.com/operasoftware/operachromiumdriver/"
                       "releases/",
            latest_release_url: str = "https://api.github.com/repos/"
                                      "operasoftware/operachromiumdriver/releases/latest",
            opera_release_tag: str = "https://api.github.com/repos/"
                                     "operasoftware/operachromiumdriver/releases/tags/{0}",
            download_manager: Optional[DownloadManager] = None,
            cache_manager: Optional[DriverCacheManager] = None,
            os_system_manager: Optional[OperationSystemManager] = None
    ):
        super().__init__(
            download_manager=download_manager,
            cache_manager=cache_manager
        )

        self.driver = OperaDriver(
            name=name,
            driver_version=version,
            url=url,
            latest_release_url=latest_release_url,
            opera_release_tag=opera_release_tag,
            http_client=self.http_client,
            os_system_manager=os_system_manager
        )

    def install(self) -> str:
        if self.driver_path is not None:
            return self.driver_path
        self.driver_path = self._get_driver_binary_path(self.driver)
        if not os.path.isfile(self.driver_path):
            for name in os.listdir(self.driver_path):
                if "sha512_sum" in name:
                    os.remove(os.path.join(self.driver_path, name))
                    break
        self.driver_path = os.path.join(self.driver_path, os.listdir(self.driver_path)[0])
        os.chmod(self.driver_path, 0o755)
        return self.driver_path
