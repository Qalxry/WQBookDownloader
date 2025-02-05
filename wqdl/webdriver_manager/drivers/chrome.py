from packaging import version

from wqdl.webdriver_manager.core.driver import Driver
from wqdl.webdriver_manager.core.logger import log
from wqdl.webdriver_manager.core.os_manager import ChromeType
import json


class ChromeDriver(Driver):

    def __init__(
            self,
            name,
            driver_version,
            url,
            latest_release_url,
            http_client,
            os_system_manager,
            chrome_type=ChromeType.GOOGLE,
            latest_patch_versions_per_build_url="https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json",
            known_good_versions_with_downloads_url="https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
    ):
        super(ChromeDriver, self).__init__(
            name,
            driver_version,
            url,
            latest_release_url,
            http_client,
            os_system_manager
        )
        self._latest_patch_versions_per_build_url = latest_patch_versions_per_build_url
        self._known_good_versions_with_downloads_url = known_good_versions_with_downloads_url
        self._browser_type = chrome_type

    def get_driver_download_url(self, os_type):
        log(f"Get {self._name} driver download url for {os_type}")
        driver_version_to_download = self.get_driver_version_to_download()
        # For Mac ARM CPUs after version 106.0.5249.61 the format of OS type changed
        # to more unified "mac_arm64". For newer versions, it'll be "mac_arm64"
        # by default, for lower versions we replace "mac_arm64" to old format - "mac64_m1".
        if version.parse(driver_version_to_download) < version.parse("106.0.5249.61"):
            os_type = os_type.replace("mac_arm64", "mac64_m1")

        if version.parse(driver_version_to_download) >= version.parse("115"):
            if os_type == "mac64":
                os_type = "mac-x64"
            if os_type in ["mac_64", "mac64_m1", "mac_arm64"]:
                os_type = "mac-arm64"

            modern_version_url = self.get_url_for_version_and_platform(driver_version_to_download, os_type)
            log(f"Modern chrome version {modern_version_url}")
            return modern_version_url

        return f"{self._url}/{driver_version_to_download}/{self.get_name()}_{os_type}.zip"

    def get_browser_type(self):
        return self._browser_type

    def get_latest_release_version(self):
        determined_browser_version = self.get_browser_version_from_os()
        log(f"Get LATEST {self._name} version for {self._browser_type}")
        if determined_browser_version is not None and version.parse(determined_browser_version) >= version.parse("115"):
            # url = "https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build.json"
            url = self._latest_patch_versions_per_build_url
            response = self._http_client.get(url)
            response_dict = json.loads(response.text)
            determined_browser_version = response_dict.get("builds").get(determined_browser_version).get("version")
            log(f"WebDriver version {determined_browser_version} selected")
            return determined_browser_version
        elif determined_browser_version is not None:
            # Remove the build version (the last segment) from determined_browser_version for version < 113
            determined_browser_version = ".".join(determined_browser_version.split(".")[:3])
            latest_release_url = f"{self._latest_release_url}_{determined_browser_version}"
        else:
            latest_release_url = self._latest_release_url

        resp = self._http_client.get(url=latest_release_url)
        log(f"Latest {self._name} version is {resp.text}")
        return resp.text.rstrip()

    def get_url_for_version_and_platform(self, browser_version, platform):
        # url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        log(f"Get URL for version {browser_version} and platform {platform}")
        url = self._known_good_versions_with_downloads_url
        response = self._http_client.get(url)
        data = response.json()
        versions = data["versions"]

        if version.parse(browser_version) >= version.parse("115"):
            short_version = ".".join(browser_version.split(".")[:3])
            compatible_versions = [v for v in versions if short_version in v["version"]]
            if compatible_versions:
                latest_version = compatible_versions[-1]
                log(f"WebDriver version {latest_version['version']} selected")
                downloads = latest_version["downloads"]["chromedriver"]
                for d in downloads:
                    if d["platform"] == platform:
                        return d["url"]
        else:
            for v in versions:
                if v["version"] == browser_version:
                    downloads = v["downloads"]["chromedriver"]
                    for d in downloads:
                        if d["platform"] == platform:
                            return d["url"]

        raise Exception(f"No such driver version {browser_version} for {platform}")
