import os
import sys
import platform
from typing import Optional

from wqdl.webdriver_manager.core.utils import (
    linux_browser_apps_to_cmd,
    windows_browser_apps_to_cmd,
    read_version_from_cmd,
)
from wqdl.webdriver_manager.core.logger import log


class ChromeType(object):
    GOOGLE = "google-chrome"
    CHROMIUM = "chromium"
    BRAVE = "brave-browser"
    MSEDGE = "edge"


class OSType(object):
    LINUX = "linux"
    MAC = "mac"
    WIN = "win"


PATTERN = {
    ChromeType.CHROMIUM: r"\d+\.\d+\.\d+",
    ChromeType.GOOGLE: r"\d+\.\d+\.\d+",
    ChromeType.MSEDGE: r"\d+\.\d+\.\d+",
    "brave-browser": r"\d+\.\d+\.\d+(\.\d+)?",
    "firefox": r"(\d+.\d+)",
}


class OperationSystemManager(object):

    def __init__(self, os_type=None):
        self._os_type = os_type
        self._browser_version = {}

    @staticmethod
    def get_os_name():
        pl = sys.platform
        if pl == "linux" or pl == "linux2":
            return OSType.LINUX
        elif pl == "darwin":
            return OSType.MAC
        elif pl == "win32" or pl == "cygwin":
            return OSType.WIN

    @staticmethod
    def get_os_architecture():
        if platform.machine().endswith("64"):
            return 64
        else:
            return 32

    def get_os_type(self):
        if self._os_type:
            return self._os_type
        return f"{self.get_os_name()}{self.get_os_architecture()}"

    @staticmethod
    def is_arch(os_sys_type):
        if "_m1" in os_sys_type:
            return True
        return platform.processor() != "i386"

    @staticmethod
    def is_mac_os(os_sys_type):
        return OSType.MAC in os_sys_type

    def set_browser_version_manually(
        self,
        browser_type,
        binary_path: Optional[str] = None,
        version: Optional[str] = None,
    ):
        """Set browser version manually."""
        assert (version or browser_type) and not (
            version and browser_type
        ), "You must provide either browser_type or version"
        if binary_path:
            log(f"Setting your {browser_type} browser version manually...")
            # 标准化路径为 Windows 绝对路径
            binary_path = os.path.abspath(binary_path)
            single_mapping = {
                OSType.LINUX: linux_browser_apps_to_cmd(binary_path),
                OSType.MAC: f"{binary_path} --version",
                OSType.WIN: windows_browser_apps_to_cmd(f"(Get-Item -Path \'{binary_path}\').VersionInfo.FileVersion"),
            }
            cmd_mapping = {
                ChromeType.GOOGLE: single_mapping,
                ChromeType.CHROMIUM: single_mapping,
                ChromeType.BRAVE: single_mapping,
                ChromeType.MSEDGE: single_mapping,  
            }
            self.get_browser_version_from_os(browser_type, cmd_mapping)
        elif version:
            log(f"Setting your {browser_type} browser version manually...")
            self._browser_version[browser_type] = version
            log(f"Your {browser_type} browser version is set to {version}")

    def get_browser_version_from_os(
        self,
        browser_type,
        cmd_mapping: Optional[dict] = None,
    ):
        """Return installed browser version."""
        log(f"Getting your {browser_type} browser version...")
        if browser_type in self._browser_version and self._browser_version[browser_type]:
            log(f"Your {browser_type} browser version is {self._browser_version[browser_type]}")
            return self._browser_version[browser_type]
        
        if cmd_mapping is None:
            cmd_mapping = {
                ChromeType.GOOGLE: {
                    OSType.LINUX: linux_browser_apps_to_cmd(
                        "google-chrome",
                        "google-chrome-stable",
                        "google-chrome-beta",
                        "google-chrome-dev",
                    ),
                    OSType.MAC: r"/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version",
                    OSType.WIN: windows_browser_apps_to_cmd(
                        r'(Get-Item -Path "$env:PROGRAMFILES\Google\Chrome\Application\chrome.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Google\Chrome\Application\chrome.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe").VersionInfo.FileVersion',
                        r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Google\Chrome\BLBeacon").version',
                        r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome").version',
                    ),
                },
                ChromeType.CHROMIUM: {
                    OSType.LINUX: linux_browser_apps_to_cmd("chromium", "chromium-browser"),
                    OSType.MAC: r"/Applications/Chromium.app/Contents/MacOS/Chromium --version",
                    OSType.WIN: windows_browser_apps_to_cmd(
                        r'(Get-Item -Path "$env:PROGRAMFILES\Chromium\Application\chrome.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Chromium\Application\chrome.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:LOCALAPPDATA\Chromium\Application\chrome.exe").VersionInfo.FileVersion',
                        r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Chromium\BLBeacon").version',
                        r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Chromium").version',
                    ),
                },
                ChromeType.BRAVE: {
                    OSType.LINUX: linux_browser_apps_to_cmd("brave-browser", "brave-browser-beta", "brave-browser-nightly"),
                    OSType.MAC: r"/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --version",
                    OSType.WIN: windows_browser_apps_to_cmd(
                        r'(Get-Item -Path "$env:PROGRAMFILES\BraveSoftware\Brave-Browser\Application\brave.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:PROGRAMFILES (x86)\BraveSoftware\Brave-Browser\Application\brave.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe").VersionInfo.FileVersion',
                        r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\BraveSoftware\Brave-Browser\BLBeacon").version',
                        r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\BraveSoftware Brave-Browser").version',
                    ),
                },
                ChromeType.MSEDGE: {
                    OSType.LINUX: linux_browser_apps_to_cmd(
                        "microsoft-edge",
                        "microsoft-edge-stable",
                        "microsoft-edge-beta",
                        "microsoft-edge-dev",
                    ),
                    OSType.MAC: r"/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --version",
                    OSType.WIN: windows_browser_apps_to_cmd(
                        # stable edge
                        r'(Get-Item -Path "$env:PROGRAMFILES\Microsoft\Edge\Application\msedge.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Microsoft\Edge\Application\msedge.exe").VersionInfo.FileVersion',
                        r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Microsoft\Edge\BLBeacon").version',
                        r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Microsoft\EdgeUpdate\Clients\{56EB18F8-8008-4CBD-B6D2-8C97FE7E9062}").pv',
                        # beta edge
                        r'(Get-Item -Path "$env:LOCALAPPDATA\Microsoft\Edge Beta\Application\msedge.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:PROGRAMFILES\Microsoft\Edge Beta\Application\msedge.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Microsoft\Edge Beta\Application\msedge.exe").VersionInfo.FileVersion',
                        r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Microsoft\Edge Beta\BLBeacon").version',
                        # dev edge
                        r'(Get-Item -Path "$env:LOCALAPPDATA\Microsoft\Edge Dev\Application\msedge.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:PROGRAMFILES\Microsoft\Edge Dev\Application\msedge.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Microsoft\Edge Dev\Application\msedge.exe").VersionInfo.FileVersion',
                        r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Microsoft\Edge Dev\BLBeacon").version',
                        # canary edge
                        r'(Get-Item -Path "$env:LOCALAPPDATA\Microsoft\Edge SxS\Application\msedge.exe").VersionInfo.FileVersion',
                        r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Microsoft\Edge SxS\BLBeacon").version',
                        # highest edge
                        r"(Get-Item (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe').'(Default)').VersionInfo.ProductVersion",
                        r"[System.Diagnostics.FileVersionInfo]::GetVersionInfo((Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe').'(Default)').ProductVersion",
                        r"Get-AppxPackage -Name *MicrosoftEdge.* | Foreach Version",
                        r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Microsoft Edge").version',
                    ),
                },
                "firefox": {
                    OSType.LINUX: linux_browser_apps_to_cmd("firefox"),
                    OSType.MAC: r"/Applications/Firefox.app/Contents/MacOS/firefox --version",
                    OSType.WIN: windows_browser_apps_to_cmd(
                        r'(Get-Item -Path "$env:PROGRAMFILES\Mozilla Firefox\firefox.exe").VersionInfo.FileVersion',
                        r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Mozilla Firefox\firefox.exe").VersionInfo.FileVersion',
                        r"(Get-Item (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe').'(Default)').VersionInfo.ProductVersion",
                        r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Mozilla\Mozilla Firefox").CurrentVersion',
                    ),
                },
            }

        try:
            cmd_mapping = cmd_mapping[browser_type][OperationSystemManager.get_os_name()]
            pattern = PATTERN[browser_type]
            version = read_version_from_cmd(cmd_mapping, pattern)
            log(f"Your {browser_type} browser version is {version}")
            self._browser_version[browser_type] = version
            return version
        except Exception:
            log(f"Can not get browser version from OS")
            raise Exception({"code": 1, "error": "Can not get browser version from OS", "browser_type": browser_type})
