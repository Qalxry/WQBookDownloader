import re
import os
import json
import glob
import shutil
import datetime

# 读取 __version__ 变量
with open("./wqdl/__init__.py", "r", encoding="utf-8") as f:
    content = f.read()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    version = match.group(1) if match else "unknown"

# 读取 UPDATE.json（如果存在）
update_file = "./UPDATE.json"
if os.path.exists(update_file):
    with open(update_file, "r", encoding="utf-8") as f:
        try:
            update_info = json.load(f)
        except json.JSONDecodeError:
            update_info = {}  # 如果 JSON 解析失败，则初始化为空字典
else:
    update_info = {}

# 更新 latest_version 字段
update_info["latest_version"] = version

# 写回 UPDATE.json
with open(update_file, "w", encoding="utf-8") as f:
    json.dump(update_info, f, indent=4)

print(f"UPDATE.json 更新完毕: latest_version = {version}")

# 3. 更新 pyproject.toml 中的 version 字段
pyproject_file = "./pyproject.toml"
if os.path.exists(pyproject_file):
    with open(pyproject_file, "r", encoding="utf-8") as f:
        pyproject_content = f.read()

    # 使用 lambda 函数替换 version 字段，避免出现无效的组引用问题
    new_pyproject_content = re.sub(
        r"(version\s*=\s*['\"])([^'\"]+)(['\"])",
        lambda m: f"{m.group(1)}{version}{m.group(3)}",
        pyproject_content,
        count=1,  # 仅替换第一个匹配项
    )

    with open(pyproject_file, "w", encoding="utf-8") as f:
        f.write(new_pyproject_content)
    print(f"pyproject.toml 更新完毕: version = {version}")
else:
    print("pyproject.toml 文件不存在")

# 找到 README.md 中的 WQBookDownloader-v{version like 2.0.0}-{win64 or linux64}.zip 链接，并替换为最新版本号
readme_file = "./README.md"
if os.path.exists(readme_file):
    with open(readme_file, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # 使用 lambda 函数替换下载链接
    new_readme_content = re.sub(
        r"(WQBookDownloader-v)(\d+\.\d+\.\d+)-(win64|linux64)(\.zip)",
        lambda m: f"{m.group(1)}{version}-{m.group(3)}{m.group(4)}",
        readme_content,
        count=0,  # 替换所有匹配项
    )

    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(new_readme_content)
    print(f"README.md 更新完毕: WQBookDownloader-v{version}-{{win64|linux64}}.zip")

# 检查是否存在 ./dist/build-YYYYMMDD 文件夹，如果存在则检查其中是否存在 WQBookDownloader-v{version}-{win64|linux64}.zip 文件
# 如果没有，则检查该目录下是否存在 WQBookDownloader ELF/EXE 文件，如果有则打包为 zip 文件
dist_folder = f"./dist/build-{datetime.datetime.now().strftime('%Y%m%d')}"
if os.path.isdir(dist_folder):
    for arch in ["win64", "linux64"]:
        zip_name = f"WQBookDownloader-v{version}-{arch}.zip"
        zip_path = os.path.join(dist_folder, zip_name)
        if not os.path.exists(zip_path):
            # 查找可能的可执行文件
            patterns = [
                os.path.join(dist_folder, "WQBookDownloader"),
                os.path.join(dist_folder, "WQBookDownloader.exe"),
            ]
            exec_files = [f for p in patterns for f in glob.glob(p)]
            if exec_files:
                shutil.make_archive(zip_path.replace(".zip", ""), "zip", dist_folder, os.path.basename(exec_files[0]))
                print(f"已打包为: {zip_name}")
