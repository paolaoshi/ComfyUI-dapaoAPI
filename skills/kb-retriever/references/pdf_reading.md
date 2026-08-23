# PDF 读取与分析

> ⚠️ **使用本文档前请注意**：本文档应在实际处理 PDF 文件之前完整阅读，以选择最合适的工具和方法。不要在未阅读本文档的情况下盲目尝试处理 PDF。

用于从 PDF 文件中提取文本、表格和元数据的方法。

## 快速决策表

| 场景 | 推荐工具 | 原因 | 命令/代码示例 |
|------|----------|------|--------------|
| 纯文本提取（最常见） | pdftotext 命令 | 最快最简单 | `pdftotext input.pdf output.txt` |
| 需要保留布局 | pdftotext -layout | 保持原始排版 | `pdftotext -layout input.pdf output.txt` |
| 需要提取表格 | pdfplumber | 表格识别能力强 | `page.extract_tables()` |
| 需要元数据 | pypdf | 轻量级 | `reader.metadata` |
| 扫描PDF（图片） | OCR (pytesseract) | 无其他选择 | 先转图片再OCR |

## 文本提取优先级

**推荐优先级（从高到低）**：
1. **pdftotext 命令行工具**（最快，适合大多数 PDF）
2. pdfplumber（适合需要保留布局或提取表格）
3. pypdf（轻量级，适合简单提取）
4. OCR（仅用于扫描PDF或无法直接提取文本的情况）

## 快速开始：使用 pdftotext（推荐）

> ⚠️ **重要**：必须将输出保存到文件，不要直接输出到终端（stdout），否则会占用大量 token！

```bash
# ✅ 正确：提取文本到文件（最快最简单）
pdftotext input.pdf output.txt

# ✅ 正确：保留布局并输出到文件
pdftotext -layout input.pdf output.txt

# ✅ 正确：提取特定页面到文件
pdftotext -f 1 -l 5 input.pdf output.txt  # 第1-5页

# ❌ 错误：不要使用 stdout（会占用大量 token）
# pdftotext input.pdf -
```

**使用流程**：
1. 使用 pdftotext 提取文本到临时文件
2. 使用 grep 或 Read 工具对生成的文本文件进行检索
3. 只读取匹配部分的上下文，而非全文

如果需要在 Python 中处理：

```python
from pypdf import PdfReader

# 读取 PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# 提取文本
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Python 库

### pypdf - 基本文本提取

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")

# 提取全部文本
for page in reader.pages:
    text = page.extract_text()
    print(text)

# 提取元数据
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Subject: {meta.subject}")
print(f"Creator: {meta.creator}")
```

### pdfplumber - 带布局的文本和表格提取

#### 提取文本（保留布局）

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### 提取表格

```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Table {j+1} on page {i+1}:")
            for row in table:
                print(row)
```

#### 高级表格提取（转为 DataFrame）

```python
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # 检查表格非空
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# 合并所有表格
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

#### 带坐标的精确文本提取

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    page = pdf.pages[0]
    
    # 提取所有字符及其坐标
    chars = page.chars
    for char in chars[:10]:  # 前10个字符
        print(f"Char: '{char['text']}' at x:{char['x0']:.1f} y:{char['y0']:.1f}")
    
    # 按边界框提取文本 (left, top, right, bottom)
    bbox_text = page.within_bbox((100, 100, 400, 200)).extract_text()
```

#### 复杂表格的高级设置

```python
import pdfplumber

with pdfplumber.open("complex_table.pdf") as pdf:
    page = pdf.pages[0]
    
    # 自定义表格提取设置
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "intersection_tolerance": 15
    }
    tables = page.extract_tables(table_settings)
    
    # 可视化调试
    img = page.to_image(resolution=150)
    img.save("debug_layout.png")
```

### pypdfium2 - 快速渲染和文本提取

```python
import pypdfium2 as pdfium

# 加载 PDF
pdf = pdfium.PdfDocument("document.pdf")

# 提取文本
for i, page in enumerate(pdf):
    text = page.get_text()
    print(f"Page {i+1} text length: {len(text)} chars")
```

#### 将 PDF 页面渲染为图片

```python
import pypdfium2 as pdfium
from PIL import Image

pdf = pdfium.PdfDocument("document.pdf")

# 渲染单页
page = pdf[0]  # 第一页
bitmap = page.render(
    scale=2.0,  # 高分辨率
    rotation=0  # 不旋转
)

# 转换为 PIL Image
img = bitmap.to_pil()
img.save("page_1.png", "PNG")

# 处理多页
for i, page in enumerate(pdf):
    bitmap = page.render(scale=1.5)
    img = bitmap.to_pil()
    img.save(f"page_{i+1}.jpg", "JPEG", quality=90)
```

## 命令行工具

### pdftotext (poppler-utils)

> ⚠️ **性能优化**：始终输出到文件，避免占用 token

```bash
# ✅ 提取文本到文件
pdftotext input.pdf output.txt

# ✅ 保留布局提取到文件
pdftotext -layout input.pdf output.txt

# ✅ 提取特定页面到文件
pdftotext -f 1 -l 5 input.pdf output.txt  # 第1-5页

# ✅ 提取带坐标的文本到 XML 文件（用于结构化数据）
pdftotext -bbox-layout document.pdf output.xml

# ❌ 避免：不要省略输出文件名（会输出到 stdout）
# pdftotext input.pdf
```

### 高级图片转换 (pdftoppm)

```bash
# 转换为 PNG，指定分辨率
pdftoppm -png -r 300 document.pdf output_prefix

# 转换特定页面范围，高分辨率
pdftoppm -png -r 600 -f 1 -l 3 document.pdf high_res_pages

# 转换为 JPEG，指定质量
pdftoppm -jpeg -jpegopt quality=85 -r 200 document.pdf jpeg_output
```

### 提取嵌入图片 (pdfimages)

```bash
# 提取所有图片
pdfimages -j input.pdf output_prefix

# 列出图片信息（不提取）
pdfimages -list document.pdf

# 以原始格式提取
pdfimages -all document.pdf images/img
```

## OCR 提取（扫描PDF）

```python
# 需要: pip install pytesseract pdf2image
import pytesseract
from pdf2image import convert_from_path

# PDF 转图片
images = convert_from_path('scanned.pdf')

# OCR 每一页
text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

## 处理加密 PDF

```python
from pypdf import PdfReader

try:
    reader = PdfReader("encrypted.pdf")
    if reader.is_encrypted:
        reader.decrypt("password")
    
    # 解密后可正常提取文本
    for page in reader.pages:
        text = page.extract_text()
        print(text)
except Exception as e:
    print(f"Failed to decrypt: {e}")
```

```bash
# 使用 qpdf 解密（需要知道密码）
qpdf --password=mypassword --decrypt encrypted.pdf decrypted.pdf

# 检查加密状态
qpdf --show-encryption encrypted.pdf
```

## 批量处理

```python
import os
import glob
from pypdf import PdfReader
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_extract_text(input_dir):
    """批量提取文本"""
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    
    for pdf_file in pdf_files:
        try:
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            output_file = pdf_file.replace('.pdf', '.txt')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Extracted text from: {pdf_file}")
            
        except Exception as e:
            logger.error(f"Failed to extract text from {pdf_file}: {e}")
            continue
```

## 性能优化

1. **文件输出优先**：始终将 pdftotext 输出保存到文件，然后用 grep/Read 检索，避免直接输出到终端占用大量 token
2. **大型PDF**：使用流式方式逐页处理，避免一次性加载整个文件
3. **文本提取**：`pdftotext` 最快；pdfplumber 适合结构化数据和表格
4. **图片提取**：`pdfimages` 比渲染页面快得多
5. **内存管理**：逐页或分块处理大文件

## 快速参考

| 任务 | 最佳工具 | 命令/代码 |
|------|----------|-----------|
| 提取文本 | pdfplumber | `page.extract_text()` |
| 提取表格 | pdfplumber | `page.extract_tables()` |
| 命令行提取 | pdftotext | `pdftotext -layout input.pdf` |
| OCR 扫描PDF | pytesseract | 先转图片再OCR |
| 提取元数据 | pypdf | `reader.metadata` |
| PDF转图片 | pypdfium2 | `page.render()` |

## 可用包

- **pypdf** - 基本操作（BSD 许可）
- **pdfplumber** - 文本和表格提取（MIT 许可）
- **pypdfium2** - 快速渲染和提取（Apache/BSD 许可）
- **pytesseract** - OCR（Apache 许可）
- **pdf2image** - PDF转图片
- **poppler-utils** - 命令行工具（GPL-2 许可）
