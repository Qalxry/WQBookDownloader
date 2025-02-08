import os
from typing import Optional
from wqdl.webdriver_manager.core.download_manager import WDMDownloadManager
from wqdl.webdriver_manager.core.driver_cache import DriverCacheManager
from wqdl.webdriver_manager.core.logger import log
from wqdl.webdriver_manager.core.os_manager import OperationSystemManager
from wqdl.webdriver_manager.core.driver import Driver

class DriverManager(object):
    def __init__(
        self, download_manager=None, cache_manager=None, os_system_manager=None
    ):
        self.driver: Driver = None
        self.driver_path = None
        self._cache_manager = cache_manager
        if not self._cache_manager:
            self._cache_manager = DriverCacheManager()

        self._download_manager = download_manager
        if self._download_manager is None:
            self._download_manager = WDMDownloadManager()
        log("====== WebDriver manager ======")

    def set_browser_version_manually(self, binary_path: str):
        browser_type = self.driver.get_browser_type()
        self._cache_manager._os_system_manager.set_browser_version_manually(
            browser_type=browser_type, binary_path=binary_path
        )
    
    def get_driver_path(self):
        return self.driver_path

    def install(self) -> str:
        if self.driver_path is None:
            self.driver_path = self._get_driver_binary_path(self.driver)
            os.chmod(self.driver_path, 0o755)
        return self.driver_path

    @property
    def http_client(self):
        return self._download_manager.http_client

    # def install(self) -> str:
    #     raise NotImplementedError("Please Implement this method")

    def _get_driver_binary_path(self, driver):
        binary_path = self._cache_manager.find_driver(driver)
        if binary_path:
            return binary_path
        log(f"Driver {driver.get_name()} not found in cache, downloading from the web")
        os_type = self.get_os_type()
        file = self._download_manager.download_file(
            driver.get_driver_download_url(os_type)
        )
        binary_path = self._cache_manager.save_file_to_cache(driver, file)
        return binary_path

    def get_os_type(self):
        return self.driver._os_system_manager.get_os_type()

    def is_installed(self) -> bool:
        binary_path = self._cache_manager.find_driver(self.driver)
        return binary_path is not None
