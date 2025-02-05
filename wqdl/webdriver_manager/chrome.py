import os
from typing import Optional

from wqdl.webdriver_manager.core.download_manager import DownloadManager
from wqdl.webdriver_manager.core.driver_cache import DriverCacheManager
from wqdl.webdriver_manager.core.manager import DriverManager
from wqdl.webdriver_manager.core.os_manager import OperationSystemManager, ChromeType
from wqdl.webdriver_manager.drivers.chrome import ChromeDriver


class ChromeDriverManager(DriverManager):
    def __init__(
        self,
        driver_version: Optional[str] = None,
        name: str = "chromedriver",
        url: str = "https://chromedriver.storage.googleapis.com",
        latest_release_url: str = "https://chromedriver.storage.googleapis.com/LATEST_RELEASE",
        chrome_type: str = ChromeType.GOOGLE,
        download_manager: Optional[DownloadManager] = None,
        cache_manager: Optional[DriverCacheManager] = None,
        os_system_manager: Optional[OperationSystemManager] = None,
        latest_patch_versions_per_build_url: str = "https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json",
        known_good_versions_with_downloads_url: str = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json",
    ):
        super().__init__(
            download_manager=download_manager,
            cache_manager=cache_manager,
            os_system_manager=os_system_manager,
        )

        self.driver = ChromeDriver(
            name=name,
            driver_version=driver_version,
            url=url,
            latest_release_url=latest_release_url,
            chrome_type=chrome_type,
            http_client=self.http_client,
            os_system_manager=os_system_manager,
            latest_patch_versions_per_build_url=latest_patch_versions_per_build_url,
            known_good_versions_with_downloads_url=known_good_versions_with_downloads_url,
        )

    def get_os_type(self):
        os_type = super().get_os_type()
        if "win" in os_type:
            return "win32"

        if not self._os_system_manager.is_mac_os(os_type):
            return os_type

        if self._os_system_manager.is_arch(os_type):
            return "mac_arm64"

        return os_type
