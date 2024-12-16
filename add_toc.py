import json
import fitz
import argparse
import os

# 解析命令行参数
parser = argparse.ArgumentParser(description="Add a table of contents to a PDF file")
parser.add_argument("pdf_path", help="Path to the PDF file")
parser.add_argument("toc_path", help="Path to the JSON file containing the table of contents")
parser.add_argument("output_path", help="Path to save the updated PDF file")
args = parser.parse_args()

pdf_path = args.pdf_path
toc_path = args.toc_path
output_path = args.output_path

# 加载 TOC JSON 数据
try:
    with open(toc_path, "r", encoding="utf-8") as f:
        toc_data = json.load(f)
        print("Loaded TOC Data")  # 打印 JSON 数据
        if "data" not in toc_data or not isinstance(toc_data["data"], list):
            raise ValueError("TOC data must be a list under the key 'data'.")
except Exception as e:
    print(f"Error loading TOC file: {e}")
    exit(1)

# 扁平化 JSON 数据
def flatten_toc(data):
    """扁平化 JSON 目录数据"""
    if not isinstance(data, list):
        raise ValueError("TOC data must be a list. Received type: {}".format(type(data).__name__))

    flat_toc = []
    for item in data:
        # 验证必需字段
        if not all(key in item for key in ("level", "label", "pnum")):
            raise ValueError(f"TOC item is missing required keys: {item}")
        
        # 转换字段类型
        try:
            level = int(item["level"])
            pnum = int(item["pnum"])
            label = str(item["label"])
        except ValueError as e:
            raise ValueError(f"Error converting TOC item fields: {item}, {e}")
        
        flat_toc.append([level, label, pnum])
        
        # 递归处理子节点
        if not item.get("isLeaf", True) and item.get("children"):
            flat_toc.extend(flatten_toc(item["children"] or []))  # 处理 null 情况
    return flat_toc

# 检查输出路径
if not os.path.exists(os.path.dirname(output_path)):
    print(f"Error: The directory for the output file {output_path} does not exist.")
    exit(1)

# 初始化 PyMuPDF
try:
    doc = fitz.open(pdf_path)
except Exception as e:
    print(f"Error: Could not open the PDF file: {e}")
    exit(1)

# 获取 JSON 数据中的目录树
try:
    toc = flatten_toc(toc_data["data"])
    print("Flattened TOC:", toc)  # 打印扁平化后的目录结构
except Exception as e:
    print(f"Error processing TOC: {e}")
    exit(1)

# 设置目录树
try:
    doc.set_toc(toc)
    doc.save(output_path)
    print(f"TOC added successfully to {output_path}.")
finally:
    doc.close()
