import os
import io
import re
import sys
import json
import time
import fitz
import shutil
import logging
import datetime
import requests
import subprocess
import urllib.parse
import traceback
import webbrowser
import platform
import flet as ft
from PIL import Image
from requests.exceptions import HTTPError
from typing import Literal, Optional, TypedDict
from selenium import webdriver
from selenium.webdriver import (
    FirefoxService,
    ChromeService,
    EdgeService,
    ChromeOptions,
    EdgeOptions,
    FirefoxOptions,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException, TimeoutException


from wqdl.webdriver_manager.chrome import ChromeDriverManager
from wqdl.webdriver_manager.firefox import GeckoDriverManager
from wqdl.webdriver_manager.microsoft import EdgeChromiumDriverManager
from wqdl.utils import JsonProxy


class ChromeDriverManagerConfig(TypedDict):
    url: str
    latest_release_url: str
    latest_patch_versions_per_build_url: str
    known_good_versions_with_downloads_url: str


class GeckoDriverManagerConfig(TypedDict):
    url: str
    latest_release_url: str
    mozila_release_download_url: str


class EdgeChromiumDriverManagerConfig(TypedDict):
    url: str
    latest_release_url: str


class WQDLConfig(JsonProxy):
    def __init__(self, json_file, mode="r", save_after_change_count=None):
        self.chrome_driver_manager_config = ChromeDriverManagerConfig(
            url="https://registry.npmmirror.com/-/binary/chromedriver",
            latest_release_url="https://registry.npmmirror.com/-/binary/chromedriver/LATEST_RELEASE",
            latest_patch_versions_per_build_url="https://gh-proxy.com/github.com/GoogleChromeLabs/chrome-for-testing/raw/refs/heads/main/data/latest-patch-versions-per-build.json",
            known_good_versions_with_downloads_url="https://gh-proxy.com/github.com/GoogleChromeLabs/chrome-for-testing/raw/refs/heads/main/data/known-good-versions-with-downloads.json",
        )
        self.gecko_driver_manager_config = GeckoDriverManagerConfig(
            url="https://gh.llkk.cc/https://github.com/mozilla/geckodriver/releases/download",
            latest_release_url="https://gh.llkk.cc/https://api.github.com/repos/mozilla/geckodriver/releases/latest",
            mozila_release_download_url="https://gh.llkk.cc/https://github.com/mozilla/geckodriver/releases/download",
        )
        self.edge_chromium_driver_manager_config = EdgeChromiumDriverManagerConfig(
            url="https://msedgedriver.azureedge.net",
            latest_release_url="https://msedgedriver.azureedge.net/LATEST_STABLE",
        )
        self.screenshot_wait = 0.1
        self.download_dir = "./downloads"
        self.user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1"
        self.login_window_size = (300, 1100)
        self.capture_window_size = (1080, 1920)
        self.force_device_scale_factor = 0.5
        self.capture_headless = True
        # "https://wqbook.wqxuetang.com/book/3248109"
        # "https://wqbook.wqxuetang.com/book/3204417"
        self.default_browser_type = "Chrome"
        self.default_search_url = ""
        self.repo_url = "https://github.com/Qalxry/WQBookDownloader"
        self.book_info_url_pattern = "https://{domain}/api/v7/read/initread?bid={bid}"
        self.page_url_pattern = "https://{domain}/deep/m/read/pdf?bid={bid}"
        self.catalog_url_pattern = (
            "https://{domain}/deep/book/v1/catatree?bid={bid}{volume_info}"
        )
        self.auto_login = False
        self.username = ""
        self.password = ""
        self.pdf_quality = 100
        self.clean_up = False
        self.starred = False
        super().__init__(json_file, mode, save_after_change_count)


logging.basicConfig(level=logging.INFO)

# 读取配置文件
CONFIG_FILE = "./configs.json"
wqdlconfig = WQDLConfig(CONFIG_FILE, "rw")
SCREENSHOT_WAIT = wqdlconfig.screenshot_wait
DOWNLOAD_DIR = wqdlconfig.download_dir
REPO_URL = "https://github.com/Qalxry/WQBookDownloader"

# 一些常量
BUTTON_HEIGHT = 60
BOOK_ITEM_HEIGHT = 150


def commit_issue(error_msg: str):
    """自动生成并打开 GitHub Issue 页面，收集完整的调试环境信息"""

    # 公共异常处理装饰器
    def safe_exec(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return f"⚠️ 信息收集失败：{str(e)}"

        return wrapper

    # 环境信息收集模块
    class EnvironmentCollector:
        @staticmethod
        @safe_exec
        def os_info():
            return (
                f"系统类型: {platform.system()} {platform.release()}\n"
                f"系统版本: {platform.version()}\n"
                f"架构: {platform.machine()}\n"
                f"处理器: {platform.processor()}"
            )

        @staticmethod
        @safe_exec
        def package_versions():
            versions = {}
            for pkg in ["requests", "selenium", "flet", "Pillow", "fitz", "PyMuPDF"]:
                try:
                    versions[pkg] = __import__(pkg).__version__
                except (ImportError, AttributeError):
                    versions[pkg] = "未安装"
            ver_str = "-  " + "\n-  ".join(f"{k}: {v}" for k, v in versions.items())
            return (
                f"Python版本: {sys.version}\n"
                f"Python解释器: {sys.executable}\n\n"
                f"#### 依赖信息:\n\n{ver_str}"
            )

        @classmethod
        def collect_all(cls):
            sections = [
                ("操作系统信息", cls.os_info()),
                ("关键依赖版本", cls.package_versions()),
            ]
            return "\n\n".join(
                f"### {title}\n\n{content}" for title, content in sections
            )

    # 错误信息处理
    error_msg = str(error_msg).strip() or "无错误信息"
    traceback_info = traceback.format_exc().strip() or "未捕获到异常堆栈"

    # 构建完整报告
    env_info = EnvironmentCollector.collect_all()
    report = (
        f"## 错误报告\n\n{time.strftime('%Y-%m-%d %H:%M:%S %z')}\n\n 错误信息：\n\n{error_msg}\n\n"
        f"## 系统诊断\n\n{env_info}\n\n"
        f"## 异常追踪\n\n```python\n{traceback_info}\n```"
    )

    # URL编码与生成
    title = f"错误报告：{error_msg.splitlines()[-1][:100]}".strip()
    encoded_url = f"{REPO_URL}/issues/new?title={urllib.parse.quote(title)}&body={urllib.parse.quote(report)}"

    # 打开浏览器
    try:
        if not webbrowser.open(encoded_url):
            raise RuntimeError("浏览器启动失败")
    except Exception:
        print(f"⛔ 自动打开失败，请手动访问：\n{encoded_url}")


def goto_star_repo():
    webbrowser.open(REPO_URL)


def open_file_manager(path=None):
    """
    跨平台打开文件管理器并定位到指定路径
    :param path: 要打开的路径（默认当前路径）
    """
    if path is None:
        path = os.getcwd()
    else:
        path = os.path.abspath(path)  # 确保路径是绝对路径

    # 根据操作系统执行不同命令
    if sys.platform == "win32" or os.name == "nt":
        # Windows系统
        try:
            os.startfile(path.replace("/", "\\"))
        except FileNotFoundError:
            print(f"路径不存在: {path}")
    elif sys.platform == "darwin":
        # macOS系统
        try:
            subprocess.run(["open", path], check=True)
        except subprocess.CalledProcessError:
            print(f"无法打开路径: {path}")
    else:
        # Linux/Unix系统
        try:
            # 尝试使用默认文件管理器
            subprocess.run(["xdg-open", path], check=True)
            return
        except:
            pass
        try:
            subprocess.run(["open", path], check=True)
        except:
            print(f"打开文件管理器失败: {path}")


# 一个打印函数被调用时间的包装器
def show_log(func):
    def wrapper(*args, **kwargs):
        print(
            f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}] {func.__name__} is called"
        )
        res = func(*args, **kwargs)
        return res

    return wrapper


@show_log
def parse_url_to_bid(url: str) -> str:
    match = re.search(r"bid=(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"/book/(\d+)", url)
    if match:
        return match.group(1)
    return ""


@show_log
def parse_domain(url: str) -> str:
    match = re.search(r"https?://([^/]+)", url)
    if match:
        return match.group(1)
    return ""


@show_log
def fetch_init_data(domain: str, bid: str) -> dict:
    res = None
    # api_url = f"https://{domain}/api/v7/read/initread?bid={bid}"
    api_url = wqdlconfig.book_info_url_pattern.format(domain=domain, bid=bid)
    res = requests.get(api_url)
    res = res.json()
    if res.get("message", None) != None:
        if res["message"] == "success" and res.get("data", None) != None:
            return res["data"]
    return None
    # raise Exception(f"获取书籍信息失败：{res}")


@show_log
def fetch(url, retries=3) -> requests.Response | None:
    for retry in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response
        except HTTPError as e:
            print(
                f"下载文件失败，状态码：{response.status_code}。重试... ({retry+1}/3)"
            )
            time.sleep(0.1)
    return None


@show_log
def build_book_item(book: dict):
    cbox = ft.Checkbox(label="", value=True, scale=1.5)
    res = ft.Container(
        ft.Card(
            ft.Row(
                col={"sm": 6},
                controls=[
                    ft.Image(
                        src=book["cover"],
                        height=BOOK_ITEM_HEIGHT,
                        border_radius=10,
                    ),
                    ft.Text(" "),
                    ft.Column(
                        controls=[
                            ft.Text(
                                f"{book['name']}",
                                theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                            ),
                            ft.Column(
                                [
                                    ft.Text(
                                        f"作者: {book['author']}",
                                        theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                                    ),
                                    ft.Text(
                                        f"页数: {book['pages']}    免费阅读页数: {book['canreadpages']}",
                                        theme_style=ft.TextThemeStyle.BODY_MEDIUM,
                                    ),
                                ],
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        height=BOOK_ITEM_HEIGHT,
                        expand=True,
                    ),
                    ft.Container(
                        cbox,
                        height=BOOK_ITEM_HEIGHT,
                        width=100,
                        border_radius=ft.BorderRadius(0, 10, 0, 10),
                        alignment=ft.Alignment(0, 0),
                        bgcolor=ft.colors.PRIMARY_CONTAINER,
                    ),
                ],
            ),
        ),
    )
    book["cbox"] = cbox
    return res


class WQBookDownloaderGUI:
    def __init__(self, page: ft.Page):
        self.book_data_list = []
        self.download_dir = DOWNLOAD_DIR
        self.page = page

        os.makedirs(self.download_dir, exist_ok=True)

        # UI setup
        self.url_input = ft.TextField(
            label="输入书籍页面的 URL (网址)",
            expand=True,
            on_submit=self.on_click_parse_button,
        )
        self.parse_button = ft.ElevatedButton(
            text="解析URL",
            height=BUTTON_HEIGHT,
            icon=ft.icons.SEARCH,
            on_click=self.on_click_parse_button,
        )
        search_bar = ft.Column(
            [
                ft.Row([self.url_input, self.parse_button]),
                ft.Container(
                    content=ft.Text(
                        "URL 类似于 https://wqbook.wqxuetang.com/book/3248109",
                        selectable=True,
                    ),
                    margin=ft.Margin(bottom=5, top=5, left=5, right=5),
                ),
            ]
        )
        self.url_input.value = wqdlconfig.default_search_url

        self.open_folder_button = ft.ElevatedButton(
            text="打开下载文件夹",
            height=BUTTON_HEIGHT,
            icon=ft.icons.FOLDER_OPEN,
            on_click=self.on_click_open_folder_button,
        )
        self.select_all_button = ft.ElevatedButton(
            text="全选",
            height=BUTTON_HEIGHT,
            icon=ft.icons.DONE,
            on_click=self.on_click_select_all_button,
        )
        self.download_button = ft.ElevatedButton(
            text="下载选中的文件",
            height=BUTTON_HEIGHT,
            icon=ft.icons.DOWNLOAD,
            bgcolor=ft.colors.PRIMARY,
            color=ft.colors.ON_PRIMARY,
            on_click=self.on_click_download_button,
        )
        self.browser_chooser = ft.Dropdown(
            label="浏览器类型 (推荐Chrome)",
            options=[
                ft.dropdown.Option("Chrome", "Chrome"),
                ft.dropdown.Option("Firefox", "Firefox"),
                ft.dropdown.Option("Edge", "Edge"),
            ],
            value=wqdlconfig.default_browser_type,
            width=250,
            on_change=self.on_change_browser_type,
        )
        button_bar = ft.Row(
            [
                self.open_folder_button,
                self.select_all_button,
                ft.Container(expand=True),
                self.browser_chooser,
                self.download_button,
            ]
        )
        self.status_text = ft.Text("", expand=True)
        status_bar = ft.Container(
            self.status_text,
            margin=ft.Margin(0, 5, 0, 10),
            width=page.window_width - page.padding.left - page.padding.right,
        )
        self.book_list_view = ft.ListView(
            [],
            height=3 * BOOK_ITEM_HEIGHT,
            expand=True,
            padding=0,
        )
        book_list_container = ft.Container(
            self.book_list_view,
            border_radius=15,
            padding=0,
            margin=0,
            height=3 * BOOK_ITEM_HEIGHT,
            expand=True,
        )
        self.query_user_memory = {}
        page.add(
            ft.Column(
                [
                    search_bar,
                    button_bar,
                    book_list_container,
                    status_bar,
                ],
                expand=True,
            )
        )

    @show_log
    def on_change_browser_type(self, e: ft.ControlEvent):
        wqdlconfig.default_browser_type = e.control.value

    @show_log
    def query_user(
        self,
        title: str = "请确认",
        content: str = "您确定进行该操作吗？",
        selections: list[str] = ["是，不再提示", "是", "否"],
        memorization: Optional[dict[str, str]] = {
            "是，不再提示": "是",
            "否，不再提示": "否",
        },
    ) -> str:
        res = None

        if content in self.query_user_memory:
            return self.query_user_memory[content]

        def close_dlg(e: ft.ControlEvent):
            nonlocal res
            res = e.control.text
            dlg_modal.open = False
            if res in memorization:
                self.query_user_memory[content] = memorization[res]
            self.page.update()

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
            content=ft.Text(content),
            actions=[
                ft.TextButton(selection, height=40, on_click=close_dlg)
                for selection in selections
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            # on_dismiss=lambda e: print("模态对话框已关闭！"),
            title_padding=ft.Padding(30, 20, 30, 0),
            content_padding=ft.Padding(30, 10, 30, 5),
            actions_padding=ft.Padding(15, 10, 15, 10),
        )
        self.page.dialog = dlg_modal
        dlg_modal.open = True
        self.page.update()
        while res is None:
            time.sleep(0.05)
        return res

    @show_log
    def query_commit_issue(self, error):
        res = self.query_user(
            "⚠️ 错误 ERROR ⚠️",
            "出现错误，可能本工具存在BUG或已失效。\n点击提交错误报告可跳转至 Github 网页来告知作者。",
            ["算了，不提交", "提交错误报告"],
        )
        if res == "提交错误报告":
            commit_issue(error)
        print(error)

    @show_log
    def get_browser_type(self) -> str:
        return self.browser_chooser.value

    @show_log
    def print_info(self, *args):
        info_str = " ".join([str(arg) for arg in args])
        info_str = info_str.strip().splitlines()[0].strip()
        if len(info_str) > 60:
            info_str = info_str[:60] + "..."
        self.status_text.value = info_str
        self.page.update()

    @show_log
    def on_click_parse_button(self, e: ft.ControlEvent):
        e.control.disabled = True
        self.page.update()
        try:
            self.book_list_view.controls.clear()
            self.book_data_list.clear()

            # 解析URL
            url = self.url_input.value.strip()
            wqdlconfig.default_search_url = url
            bid = parse_url_to_bid(url)
            if bid == "":
                self.print_info("无法解析该URL")
                self.query_user("警告", "无法解析该URL，请检查输入是否正确", ["确认"])
                e.control.disabled = False
                self.page.update()
                return

            # 获取书籍信息
            domain = parse_domain(url)
            init_data = fetch_init_data(domain, bid)
            if not init_data:
                self.print_info("获取书籍信息失败")
                self.query_user(
                    "警告", "获取书籍信息失败，请检查网络连接和URL", ["确认"]
                )
                e.control.disabled = False
                self.page.update()
                return

            # 处理书籍信息
            book_name = init_data.get("name", "未知书籍")
            book_author = init_data.get("author", "未知作者")
            is_multivolumed = init_data.get("ismultivolumed", 0) == 1

            # 构建书籍列表
            if is_multivolumed:
                for vol in init_data["volume_list"]:
                    new_item = {
                        "domain": domain,
                        "bid": vol["bid"],
                        "volume_no": vol["number"],
                        "author": book_author,
                        "name": vol["name"],
                        "pages": vol["pages"],
                        "cover": vol["cover"],
                        "canreadpages": vol["canreadpages"],
                    }
                    # 检查一下是否已经存在
                    exists = False
                    for item in self.book_data_list:
                        if str(item) == str(new_item):
                            exists = True
                            break
                    if not exists:
                        self.book_data_list.append(new_item)
                        self.book_list_view.controls.append(build_book_item(new_item))
            else:
                new_item = {
                    "domain": domain,
                    "bid": init_data["bid"],
                    "volume_no": None,
                    "author": book_author,
                    "name": book_name,
                    "pages": init_data.get("pages", 0),
                    "cover": init_data.get("coverurl", ""),
                    "canreadpages": init_data.get("canreadpages", 0),
                }
                # 检查一下是否已经存在
                exists = False
                for item in self.book_data_list:
                    if str(item) == str(new_item):
                        exists = True
                        break
                if not exists:
                    self.book_data_list.append(new_item)
                    self.book_list_view.controls.append(build_book_item(new_item))
            self.print_info(f"解析成功，共找到 {len(self.book_data_list)} 本书籍")
        except Exception as e:
            self.query_commit_issue(e)
        finally:
            e.control.disabled = False
            self.page.update()

    @show_log
    def waiting_dialog(
        self,
        title: str = "请稍候",
        content: str = "等待处理完成...",
    ):
        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text(title, theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
            content=ft.Text(content),
            actions=[],
            title_padding=ft.Padding(30, 20, 30, 0),
            content_padding=ft.Padding(30, 10, 30, 5),
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()
        return dlg

    @show_log
    def close_waiting_dialog(self):
        self.page.dialog.open = False
        self.page.update()

    @show_log
    def on_click_open_folder_button(self, e):
        open_file_manager(self.download_dir)
        self.page.update()

    @show_log
    def on_click_select_all_button(self, e):
        flag = False
        # 检查是否已经全选，如果已经全选则取消全选
        for item in self.book_data_list:
            if not item["cbox"].value:
                flag = True
                break
        for item in self.book_data_list:
            item["cbox"].value = flag
        self.page.update()

    @show_log
    def on_click_download_button(self, e):
        e.control.disabled = True
        self.page.update()
        if len(self.book_data_list) == 0:
            self.query_user("提示", "请先解析书籍 URL", ["确认"])
            e.control.disabled = False
            self.page.update()
            return
        try:
            for item in self.book_data_list:
                if item["cbox"].value:
                    download_book(self, item)
        except Exception as err:
            self.query_commit_issue(err)
            e.control.disabled = False
            self.page.update()
            return
        self.print_info("下载完成")
        res = self.query_user("提示", "下载完成，是否打开下载文件夹？")
        if res == "是":
            open_file_manager(self.download_dir)
        e.control.disabled = False
        self.page.update()

        if not wqdlconfig.starred:
            res = self.query_user(
                "❤️赞赏❤️",
                "如果您觉得本工具好用，请给作者一个 Star ~⭐️",
                ["太垃圾了，不给", "赏个 Star"],
            )
            if res == "赏个 Star":
                wqdlconfig.starred = True
                goto_star_repo()
                self.query_user("🌹感谢🌹", "感谢您的支持！", ["确认"])
            else:
                for i in range(1, 10):
                    self.query_user("?" * i, "😭" * i, ["就不给😛", "好吧😒"])
                    if res == "好吧😒":
                        wqdlconfig.starred = True
                        goto_star_repo()
                        self.query_user("🌹感谢🌹", "感谢您的支持！", ["确认"])
                        break


class WQBookDownloader:
    def __init__(self, book: dict, gui_handler, download_dir: str = "./downloads"):
        self.driver = None
        self.book = book
        self.download_dir = download_dir
        self.book_dir = os.path.join(
            download_dir, f"{book['bid']}_{book['name']}"
        )  # 书籍下载目录
        self.image_dir = os.path.join(self.book_dir, "images")  # 临时图片保存目录
        self.gui: WQBookDownloaderGUI = gui_handler
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.book_dir, exist_ok=True)
        os.makedirs(self.image_dir, exist_ok=True)

    # Step 1-2 / 2-1
    @show_log
    def setup_driver(
        self,
        headless=False,
        window_size: Literal["maximized", "mobile"] = "maximized",
    ):
        browserType = self.gui.get_browser_type()
        if browserType == "Chrome":
            options = ChromeOptions()
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument(f"--user-agent={wqdlconfig.user_agent}")
            if headless:
                options.add_argument("--headless=new")
                options.add_argument(
                    f"--force-device-scale-factor={wqdlconfig.force_device_scale_factor}"
                )
                # options.add_argument("user-data-dir=selenium")
                # options.add_argument("--window-size=1600,2160")
            else:
                options.add_argument("--start-maximized")

            driver_manager = ChromeDriverManager(
                # url="https://registry.npmmirror.com/-/binary/chromedriver",
                # latest_release_url="https://registry.npmmirror.com/-/binary/chromedriver/LATEST_RELEASE",
                # latest_patch_versions_per_build_url="https://gh-proxy.com/github.com/GoogleChromeLabs/chrome-for-testing/raw/refs/heads/main/data/latest-patch-versions-per-build.json",
                # known_good_versions_with_downloads_url="https://gh-proxy.com/github.com/GoogleChromeLabs/chrome-for-testing/raw/refs/heads/main/data/known-good-versions-with-downloads.json",
                **wqdlconfig.chrome_driver_manager_config,
            )
            if not driver_manager.is_installed():
                self.gui.waiting_dialog(
                    "请稍候", f"未检测到 {browserType} 浏览器驱动，正在下载..."
                )
                self.gui.print_info(f"正在下载 {browserType} 浏览器驱动，请稍候...")
                driver_manager.install()
                self.gui.print_info(f"{browserType} 浏览器驱动下载完成")
                self.gui.close_waiting_dialog()

            self.driver = webdriver.Chrome(
                service=ChromeService(driver_manager.get_driver_path()),
                options=options,
            )

        elif browserType == "Firefox":
            options = FirefoxOptions()
            options.set_preference("general.useragent.override", wqdlconfig.user_agent)
            if headless:
                options.add_argument("-headless")
                options.set_preference(
                    "layout.css.devPixelsPerPx",
                    str(1 / wqdlconfig.force_device_scale_factor),
                )

            driver_manager = GeckoDriverManager(
                # url="https://gh.llkk.cc/https://github.com/mozilla/geckodriver/releases/download",
                # latest_release_url="https://gh.llkk.cc/https://api.github.com/repos/mozilla/geckodriver/releases/latest",
                # mozila_release_download_url="https://gh.llkk.cc/https://github.com/mozilla/geckodriver/releases/download",
                **wqdlconfig.gecko_driver_manager_config,
            )
            if not driver_manager.is_installed():
                self.gui.waiting_dialog(
                    "请稍候", f"未检测到 {browserType} 浏览器驱动，正在下载..."
                )
                self.gui.print_info(f"正在下载 {browserType} 浏览器驱动，请稍候...")
                driver_manager.install()
                self.gui.print_info(f"{browserType} 浏览器驱动下载完成")
                self.gui.close_waiting_dialog()

            self.driver = webdriver.Firefox(
                service=FirefoxService(driver_manager.get_driver_path()),
                options=options,
            )
            self.driver.maximize_window()

        elif browserType == "Edge":
            options = EdgeOptions()
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument(f"--user-agent={wqdlconfig.user_agent}")
            if headless:
                options.add_argument("--headless=new")
                options.add_argument(
                    f"--force-device-scale-factor={wqdlconfig.force_device_scale_factor}"
                )
            else:
                options.add_argument("--start-maximized")

            driver_manager = EdgeChromiumDriverManager(
                **wqdlconfig.edge_chromium_driver_manager_config
            )
            if not driver_manager.is_installed():
                self.gui.waiting_dialog(
                    "请稍候", f"未检测到 {browserType} 浏览器驱动，正在下载..."
                )
                self.gui.print_info(f"正在下载 {browserType} 浏览器驱动，请稍候...")
                driver_manager.install()
                self.gui.print_info(f"{browserType} 浏览器驱动下载完成")
                self.gui.close_waiting_dialog()

            self.driver = webdriver.Edge(
                service=EdgeService(driver_manager.get_driver_path()),
                options=options,
            )

        if window_size == "mobile":
            self.driver.set_window_size(*wqdlconfig.login_window_size)
            # self.driver.set_window_size(300, 1100)
        elif window_size == "maximized":
            self.driver.set_window_size(*wqdlconfig.capture_window_size)
            # self.driver.set_window_size(1080, 1920)
            # print(self.driver.get_window_size())

    # Step 1-2
    @show_log
    def save_cookies(self):
        # return True
        cookies = self.driver.get_cookies()
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)
        self.gui.print_info("登录 cookies 已保存！")

    # Step 2-2
    @show_log
    def load_cookies(self, check_only=False):
        # return True
        if os.path.exists("cookies.json"):
            if check_only:  # 仅检查是否存在
                return True
            # self.driver.get(f"https://{self.book['domain']}")
            with open("cookies.json", "r") as f:
                cookies = json.load(f)
                for cookie in cookies:
                    # cookie.pop("domain", None)  # 去除 cookie 中的 domain 字段，否则无法添加
                    self.driver.add_cookie(cookie)
            self.gui.print_info("Cookies 已加载")
            return True
        return False

    # Step 1
    @show_log
    def login_workflow(self):
        self.gui.query_user(
            "提示", "接下来点击确认将打开浏览器，请手动登录后再返回此窗口", ["确认"]
        )
        self.gui.print_info("请完成手动登录操作...")
        self.gui.waiting_dialog("请稍候", "等待完成登录操作，请勿直接关闭窗口...")
        try:
            self.setup_driver(headless=False, window_size="mobile")
            self.driver.get(
                # f"https://{self.book['domain']}/deep/m/read/pdf?bid={self.book['bid']}"
                wqdlconfig.page_url_pattern.format(
                    domain=self.book["domain"], bid=self.book["bid"]
                )
            )
            # 等待并关闭引导提示
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".e_tip"))
            ).click()
            time.sleep(0.2)

            # 点击购物车按钮
            # document.body.querySelector(".cart-btn").click()
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".cart-btn"))
            ).click()
            time.sleep(0.2)
            # self.driver.execute_script("document.body.querySelector('.cart-btn').click()")

            # # 点击书签按钮
            # WebDriverWait(self.driver, 10).until(
            #     EC.element_to_be_clickable((By.CSS_SELECTOR, ".page-m-mark"))
            # ).click()
            # time.sleep(0.2)

            # 处理弹窗
            buttons = self.driver.find_elements(By.CSS_SELECTOR, ".fui-button")
            for btn in buttons:
                if btn.text == "确定":
                    btn.click()
                    break

            time.sleep(0.2)
            if wqdlconfig.auto_login:
                # 自动输入用户名密码
                # 用户名 input
                self.driver.execute_script(
                    f"""
                    input_list = document.body.querySelectorAll("input")
                    input_list[0].value = "{wqdlconfig.username}";
                    input_list[0].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input_list[1].value = "{wqdlconfig.password}";
                    input_list[1].dispatchEvent(new Event('input', {{ bubbles: true }}));
                    """
                )
                time.sleep(0.5)
                self.driver.execute_script(
                    f"""
                    document.body.querySelector(".mint-button.ableBtn")?.click();
                    """
                )
                time.sleep(3)
            else:
                while True:
                    time.sleep(3)
                    if self.driver.current_url.startswith(
                        # f"https://{self.book['domain']}/deep/m/read/pdf"
                        wqdlconfig.page_url_pattern.format(
                            domain=self.book["domain"], bid=self.book["bid"]
                        )
                    ):
                        break

        except NoSuchWindowException:
            self.gui.query_user("提示", "登录失败", ["确认"])
            return False

        time.sleep(2)  # 等待页面加载完成
        self.save_cookies()
        self.driver.quit()
        self.gui.close_waiting_dialog()
        self.gui.query_user(
            "提示",
            "登录成功！cookies 已缓存至 cookies.json，接下来将开始书籍下载",
            ["确认"],
        )
        return True

    # Step 2
    @show_log
    def capture_pages(self) -> str:
        self.gui.waiting_dialog("请稍候", "正在截取书籍页面，请勿关闭窗口...")
        self.book["downloaded_pages"] = 0
        self.setup_driver(headless=wqdlconfig.capture_headless, window_size="maximized")
        # self.driver.get(f"https://{self.book['domain']}/deep/m/read/pdf?bid={self.book['bid']}")

        flag = False

        def init():
            nonlocal flag
            self.driver.get(
                wqdlconfig.page_url_pattern.format(
                    domain=self.book["domain"], bid=self.book["bid"]
                )
            )
            time.sleep(1)
            self.load_cookies()
            # self.driver.get(f"https://{self.book['domain']}/deep/m/read/pdf?bid={self.book['bid']}")
            self.driver.get(
                wqdlconfig.page_url_pattern.format(
                    domain=self.book["domain"], bid=self.book["bid"]
                )
            )

            # 等待 class=".e_tip" 元素出现并点击（点击屏幕中央出现的指导页）
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".e_tip"))
                ).click()
            except TimeoutException:
                # 说明没有指导页，直接跳过
                pass

            # 获取书籍信息
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".perc"))
            )
            time.sleep(2)
            self.driver.find_element(By.CSS_SELECTOR, ".perc")
            self.driver.find_element(By.CSS_SELECTOR, ".e_title span")

            # document.body.querySelector('#readWarn')
            if self.driver.find_elements(By.ID, "readWarn") != []:
                flag = True
                res = self.gui.query_user(
                    content=f"该书籍为付费书籍，但似乎您未购买，将只能截取前 {self.book['canreadpages']} 页。\n（或者登录状态已失效）",
                    selections=["重新登录", "继续截取", "返回"],
                )
                if res == "返回":
                    self.driver.quit()
                    return res
                elif res == "重新登录":
                    self.driver.quit()
                    return res
                else:
                    self.gui.waiting_dialog(
                        "请稍候", "正在截取书籍页面，请勿关闭窗口..."
                    )
            else:
                flag = False
            return "继续截取"

        res = init()
        if res == "返回" or res == "重新登录":
            return res

        # 截图每一页
        start_time = time.time()
        for page_num in range(1, self.book["pages"] + 1):
            img_path = os.path.join(self.image_dir, f"image{page_num}.png")
            if os.path.exists(img_path):
                self.gui.print_info(f"第 {page_num} 页已存在，跳过")
                continue
            for retry in range(4):
                try:
                    if flag and page_num > self.book["canreadpages"]:
                        self.gui.print_info("已到达可阅读页数")
                        raise Exception("已到达可阅读页数")

                    element_id = f"pageImgBox{page_num}"
                    # self.driver.execute_script(f"document.getElementById('{element_id}').style.zoom='200%';")  # 放大页面
                    self.driver.execute_script(
                        f"document.getElementById('{element_id}')?.scrollIntoView({{behavior: 'instant', block: 'center', inline: 'nearest'}});"
                    )
                    time.sleep(SCREENSHOT_WAIT)

                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, f"#{element_id} uni-view.page-lmg img")
                        )
                    )
                    time.sleep(SCREENSHOT_WAIT)

                    element = self.driver.find_element(By.ID, element_id)
                    # self.driver.execute_script(f"document.getElementById('{element_id}').style.zoom='200%';")  # 放大页面
                    # print(element.size)

                    # 缩放页面
                    # element = self.driver.find_element(By.CSS_SELECTOR, f"#{element_id} uni-view.page-lmg")
                    element.screenshot(img_path)
                    self.gui.print_info(
                        f"第 {page_num} 页截图保存成功，预计剩余时间：{(time.time()-start_time)/(page_num+1)*(self.book['pages']-page_num):.2f} 秒"
                    )
                    break
                except Exception as e:
                    if page_num == self.book["canreadpages"] + 1 or flag:
                        res = self.gui.query_user(
                            content=f"已到达可阅读页数 {self.book['canreadpages']}。\n可能您未购买该电子书，或者登录状态已失效。\n如果您已购买，请尝试重新登录。",
                            selections=["重新登录", "继续生成PDF"],
                        )
                        if res == "重新登录":
                            self.driver.quit()
                            return res
                        self.gui.waiting_dialog(
                            "请稍候", "正在释放资源，请勿关闭窗口..."
                        )
                        self.book["downloaded_pages"] = page_num - 1
                        self.driver.quit()
                        return res
                    elif page_num != 1 and retry < 3:
                        self.gui.print_info(
                            f"第 {page_num} 页截取失败，重试中... ({retry+1}/4)"
                        )
                        time.sleep(0.5)
                        res = init()
                        if res == "返回" or res == "重新登录":
                            return res
                    else:
                        self.gui.print_info(f"第 {page_num} 页截取失败，错误：{e}")
                        raise e

        self.book["downloaded_pages"] = self.book["pages"]
        self.driver.quit()
        self.gui.close_waiting_dialog()
        self.gui.print_info(f"{self.book['name']} 所有页面截取已完成")

    # # Step 3
    # @show_log
    # def create_pdf(self):
    #     self.gui.waiting_dialog("请稍候", "正在生成 PDF，请勿关闭窗口...")
    #     output_path = os.path.join(
    #         self.book_dir, f"{self.book['bid']}_{self.book['name']}.pdf"
    #     )
    #     doc = fitz.open()

    #     for page_num in range(1, self.book["downloaded_pages"] + 1):
    #         img_path = os.path.join(self.image_dir, f"image{page_num}.png")
    #         with Image.open(img_path) as img:
    #             pdf_page = doc.new_page(width=img.width, height=img.height)
    #             pdf_page.insert_image((0, 0, img.width, img.height), filename=img_path)
    #             time.sleep(0.001)

    #     doc.save(output_path)
    #     self.gui.print_info(f"PDF已生成：{output_path}")
    #     self.book["pdf_path"] = output_path
    #     self.gui.close_waiting_dialog()
    #     return output_path

    @show_log
    def create_pdf(self):
        self.gui.waiting_dialog("请稍候", "正在生成 PDF，请勿关闭窗口...")
        output_path = os.path.join(
            # self.book_dir, f"{self.book['bid']}_{self.book['name']}.pdf"
            self.download_dir,
            f"{self.book['name']}.pdf",
        )
        if os.path.exists(output_path):
            res = self.gui.query_user(
                "提示",
                f"PDF文件已存在，是否覆盖？\n{output_path}",
                ["取消", "覆盖", "并存"],
            )
            if res == "取消":
                return res
            elif res == "覆盖":
                os.remove(output_path)
            else:
                output_path = os.path.join(
                    self.download_dir,
                    f"{self.book['name']}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf",
                )
            self.gui.waiting_dialog("请稍候", "正在生成 PDF，请勿关闭窗口...")

        doc = fitz.open()
        for page_num in range(1, self.book["downloaded_pages"] + 1):
            img_path = os.path.join(self.image_dir, f"image{page_num}.png")
            with Image.open(img_path) as img:
                # 处理含有透明通道的PNG（转换为白色背景）
                if img.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")

                # 将图片转换为JPEG格式并压缩（质量设为85%）
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format="JPEG", quality=wqdlconfig.pdf_quality)
                img_byte_arr.seek(0)

                # 创建PDF页面并插入压缩后的图片
                pdf_page = doc.new_page(width=img.width, height=img.height)
                pdf_page.insert_image(
                    rect=(0, 0, img.width, img.height),
                    stream=img_byte_arr,  # 使用内存中的JPEG流
                )
                time.sleep(0.001)

        # 保存PDF时启用压缩和优化选项
        doc.save(
            output_path,
            garbage=3,  # 删除未使用的对象
            deflate=True,  # 启用压缩
            clean=True,  # 优化文件结构
        )
        self.gui.print_info(f"PDF已生成：{output_path}")
        self.book["pdf_path"] = output_path
        self.gui.close_waiting_dialog()
        return output_path

    # Step 4
    @show_log
    def add_toc(self, pdf_path, toc_data, output_path: Optional[str] = None):
        self.gui.print_info("正在添加目录到 PDF...")
        self.gui.waiting_dialog("请稍候", "正在添加目录到 PDF，请勿关闭窗口...")

        # if output_path is None:
        #     output_path = pdf_path

        def flatten_toc(data):
            flat_toc = []
            for item in data:
                flat_toc.append([int(item["level"]), item["label"], int(item["pnum"])])
                if not item["isLeaf"] and item["children"]:
                    flat_toc.extend(flatten_toc(item["children"]))
            return flat_toc

        try:
            doc = fitz.open(pdf_path)
            toc = flatten_toc(toc_data)
            doc.set_toc(toc)
            if output_path is None or os.path.abspath(output_path) == os.path.abspath(pdf_path):
                output_path = pdf_path + ".temp.pdf"
                doc.save(output_path)
                doc.close()
                os.remove(pdf_path)
                os.rename(output_path, pdf_path)
            else:
                doc.save(output_path)
                doc.close()
                
            self.gui.close_waiting_dialog()
            self.gui.print_info(f"已添加目录到PDF：{output_path}")
        except Exception as e:
            self.gui.query_commit_issue(e)
            return

    # Step 4-2
    @show_log
    def fetch_toc(self):
        # https://wqbook.wqxuetang.com/deep/book/v1/catatree?bid=3248109&volume_no=1
        # catalog_url = f"https://{self.book['domain']}/deep/book/v1/catatree?bid={self.book['bid']}{'&volume_no='+str(self.book['volume_no']) if self.book['volume_no'] else ''}"
        catalog_url = wqdlconfig.catalog_url_pattern.format(
            domain=self.book["domain"],
            bid=self.book["bid"],
            volume_info=(
                f"&volume_no={self.book['volume_no']}" if self.book["volume_no"] else ""
            ),
        )
        catalog_path = os.path.join(self.book_dir, "catalog.json")
        catalog_data = None
        if os.path.exists(catalog_path):
            self.gui.print_info(
                f"{'第'+str(self.book['volume_no'])+'卷的' if self.book['volume_no'] else ''}目录文件已存在，跳过下载目录文件步骤"
            )
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog_data = json.load(f)
        else:
            self.gui.print_info(
                f"下载{'第'+str(self.book['volume_no'])+'卷的' if self.book['volume_no'] else ''}目录文件..."
            )
            catalog_data = fetch(catalog_url).json().get("data", None)
            if catalog_data is not None:
                with open(catalog_path, "w", encoding="utf-8") as f:
                    json.dump(catalog_data, f, indent=2)
                self.gui.print_info(
                    f"{'第'+str(self.book['volume_no'])+'卷的' if self.book['volume_no'] else ''}目录数据已保存到: {catalog_path}"
                )
            else:
                self.gui.print_info(
                    f"下载{'第'+str(self.book['volume_no'])+'卷的' if self.book['volume_no'] else ''}目录文件失败，将无法生成目录"
                )
        self.book["toc_data"] = catalog_data
        return catalog_data

    # Main
    @show_log
    def run(self):
        if (
            not self.load_cookies(check_only=True)
            or self.gui.query_user(
                content="是否使用上次登录的状态？\n(如果登录时间过长，可能会失效，需要重新登录)"
            )
            == "否"
        ):
            if not self.login_workflow():
                return
            time.sleep(0.1)

        res = self.capture_pages()

        while res == "重新登录":
            self.login_workflow()
            res = self.capture_pages()

        if self.book["downloaded_pages"] == 0:
            # raise Exception("未获取到任何页面截图，请检查是否登录状态失效或其他原因")
            self.gui.print_info(
                "未获取到任何页面截图，请检查是否登录状态失效或其他原因"
            )
            return
        elif (
            self.book["downloaded_pages"] != self.book["pages"]
            and self.gui.query_user(
                content=f"仅获取到 {self.book['downloaded_pages']} 页，是否继续生成 PDF？",
                selections=["是", "否"],
            )
            == "否"
        ):
            return

        # 生成PDF
        pdf_path = self.create_pdf()
        if pdf_path in ["取消", "返回"]:
            return

        toc_data = self.fetch_toc()
        if toc_data is not None and self.book["downloaded_pages"] == self.book["pages"]:
            self.add_toc(pdf_path, toc_data)

        # 清理临时文件
        if wqdlconfig.clean_up and os.path.exists(self.image_dir):
            self.gui.print_info("清理临时文件...")
            if os.path.exists(self.book_dir):
                shutil.rmtree(self.book_dir)

        self.gui.print_info(
            f"{self.book['name']} 下载完成, 文件夹：{self.download_dir}"
        )


@show_log
def download_book(gui_handler: WQBookDownloaderGUI, book: dict):
    # 1. 创建下载器
    downloader = WQBookDownloader(
        book, gui_handler=gui_handler, download_dir=DOWNLOAD_DIR
    )
    downloader.run()


if __name__ == "__main__":

    def main(page: ft.Page):
        page.fonts = {"Noto Sans SC": "NotoSansSC-Regular.ttf"}
        page.theme = ft.Theme(font_family="Noto Sans SC")
        page.window_height = 700
        page.window_min_height = 700
        page.window_max_height = 700
        page.window_width = 900
        page.window_min_width = 900
        page.window_max_width = 900
        page.window_maximizable = False
        page.window_minimizable = False
        page.update()
        page.window_center()
        page.padding = ft.Padding(20, 30, 20, 0)
        page.title = "WQBookDownloader 文泉书库下载器"
        WQBookDownloaderGUI(page)
        page.window_visible = True  # 显示窗口
        page.update()
        page.window_resizable = False
        page.update()

    # 先创建一个隐藏的窗口，加载完成后再显示
    ft.app(target=main, view=ft.AppView.FLET_APP_HIDDEN)
