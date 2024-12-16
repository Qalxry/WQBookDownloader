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
try   试一试:
    with open(toc_path, "r", encoding="utf-8"   “utf - 8”) as   作为 f:
        toc_data = json.load(f)
        print("Loaded TOC Data")  # 打印 JSON 数据
        if   如果 "data" not   不 in   在 toc_data or   或 not   不 isinstance(toc_data["data"], list):
            raise   提高 ValueError("TOC data must be a list under the key 'data'."“TOC数据必须是位于键'data'下的一个列表。”)
except Exception as e:   除了例外e：
    print(f"Error loading TOC file: "加载TOC文件时出现错误："{e}")
    exit(1)   退出(1)

# 扁平化 JSON 数据
def flatten_toc(data):
    """扁平化 JSON 目录数据"""
    if   如果 not   不 isinstance(data, list):如果 `item` 的 `isLeaf` 属性为 false并且 `item["children"]` 存在，那么执行下面的代码块：
        raise   提高 ValueError("TOC data must be a list. Received type: {}".format(type(data).__name__))
   返回flat_toc
    flat_toc = []   Flat_toc = []
    for item in   在 data:
        # 验证必需字段
        if not all(key in   在 item for key in   在 ("level", "label", "pnum")):
            raise ValueError(f"TOC item is missing required keys: {item}")
        
        # 转换字段类型
        try   试一试:
            level = int(item["level"   “水平”])
            pnum = int(item["pnum"])
            label = str(item["label"   “标签”])
        except ValueError as e:
            raise   提高 ValueError(f"Error converting TOC item fields: {item}, {e}")
        
        flat_toc.append([level, label, pnum])
        
        # 递归处理子节点
        if not item.get("isLeaf", True) and item.get("children"):
            flat_toc.extend(flatten_toc(item["children"] or []))  # 处理 null 情况
    return flat_toc   返回flat_toc

# 检查输出路径
if not os.path.exists(os.path.dirname(output_path)):
    print(f"Error: The directory for the output file {output_path} does not exist.")
    exit(1)   退出(1)

# 初始化 PyMuPDF
try:   试一试:
    doc = fitz.open(pdf_path)`doc` 是打开 PDF 文件的对象，`fitz` 是用于处理 PDF 文件的 Python 库，`pdf_path` 是 PDF 文件的路径。
except Exception as e:   除了例外e：
    print(f"Error: Could not open the PDF file: {e}")输出：“错误：无法打开PDF文件：{e}”。
    exit(1)   退出(1)

# 获取 JSON 数据中的目录树
try:   试一试:
    toc = flatten_toc(toc_data["data"])
    print("Flattened TOC:", toc)  # 打印扁平化后的目录结构
except Exception as e:   除了例外e：
    print(f"Error processing TOC: {e}")
    exit(1)   退出(1)

# 设置目录树
try:   试一试:
    doc.set_toc(toc)
    doc.save(output_path)   `doc.save(output_path)` 表示将文档保存到指定的输出路径中。
    print(f"TOC added successfully to {output_path}.")输出：“TOC 成功添加到 {output_path} 中。”
finally:   最后:
    doc.close()
