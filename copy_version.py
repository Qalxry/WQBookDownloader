import re
import json
import os

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
        count=1  # 仅替换第一个匹配项
    )

    with open(pyproject_file, "w", encoding="utf-8") as f:
        f.write(new_pyproject_content)
    print(f"pyproject.toml 更新完毕: version = {version}")
else:
    print("pyproject.toml 文件不存在")