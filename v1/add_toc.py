# add_toc.py

import json
import fitz
import argparse

# 解析命令行参数
parser = argparse.ArgumentParser(description="Add a table of contents to a PDF file")
parser.add_argument("pdf_path", help="Path to the PDF file")
parser.add_argument(
    "toc_path",
    help="Path to the JSON file containing the table of contents",
)
parser.add_argument("output_path", help="Path to save the updated PDF file")
args = parser.parse_args()

pdf_path = args.pdf_path
toc_path = args.toc_path
output_path = args.output_path

# 假设 JSON 数据存储在一个名为 `toc.json` 的文件中
with open(toc_path, "r", encoding="utf-8") as f:
    toc_data = json.load(f)


# 扁平化 JSON 数据
def flatten_toc(data):
    flat_toc = []
    for item in data:
        flat_toc.append([int(item["level"]), item["label"], int(item["pnum"])])
        if not item["isLeaf"] and item["children"]:
            flat_toc.extend(flatten_toc(item["children"]))
    return flat_toc


# 初始化 PyMuPDF
doc = fitz.open(pdf_path)

# 获取 JSON 数据中的目录树
toc = flatten_toc(toc_data["data"])

# 设置目录树
doc.set_toc(toc)

# 保存修改后的 PDF
doc.save(output_path)
doc.close()

