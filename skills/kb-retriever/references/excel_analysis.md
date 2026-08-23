# Excel 数据分析

> ⚠️ **使用本文档前请注意**：本文档应在实际分析 Excel 数据之前阅读，以了解正确的 pandas 分析方法。请先阅读 excel_reading.md 学习如何读取数据。

使用 pandas 对 Excel 数据进行常规分析操作。

## 快速参考

| 任务 | 常用方法 | 代码示例 |
|------|----------|----------|
| 按条件过滤 | 布尔索引 | `df[df['sales'] > 10000]` |
| 分组聚合 | groupby | `df.groupby('region')['sales'].sum()` |
| 排序 | sort_values | `df.sort_values('sales', ascending=False)` |
| 计算新列 | 直接赋值 | `df['profit'] = df['revenue'] - df['cost']` |
| 统计汇总 | describe | `df.describe()` |

## 分组聚合（GroupBy）

```python
import pandas as pd

df = pd.read_excel("sales.xlsx")

# 按列分组并聚合
sales_by_region = df.groupby("region")["sales"].sum()
print(sales_by_region)

# 多列分组和多重聚合
result = df.groupby(["region", "product"]).agg({
    "sales": "sum",
    "quantity": "count",
    "price": "mean"
})
```

## 数据过滤

```python
# 按条件过滤行
high_sales = df[df["sales"] > 10000]

# 多条件过滤
filtered = df[(df["sales"] > 10000) & (df["region"] == "North")]

# 使用 isin 过滤
selected = df[df["product"].isin(["A", "B", "C"])]
```

## 派生指标计算

```python
# 计算新列
df["profit_margin"] = (df["revenue"] - df["cost"]) / df["revenue"]

# 百分比计算
df["growth_rate"] = (df["current"] - df["previous"]) / df["previous"] * 100

# 累计求和
df["cumulative_sales"] = df["sales"].cumsum()
```

## 排序

```python
# 按单列排序
df_sorted = df.sort_values("sales", ascending=False)

# 按多列排序
df_sorted = df.sort_values(["region", "sales"], ascending=[True, False])
```

## 数据透视表

```python
# 创建数据透视表
pivot = pd.pivot_table(
    df,
    values="sales",
    index="region",
    columns="product",
    aggfunc="sum",
    fill_value=0
)

print(pivot)
```

## 统计分析

```python
# 基本统计
print(df.describe())

# 特定列统计
print(df["sales"].mean())
print(df["sales"].median())
print(df["sales"].std())

# 计数统计
print(df["category"].value_counts())
```

## 数据合并

```python
# 垂直合并多个 DataFrame
combined = pd.concat([df1, df2], ignore_index=True)

# 按公共列合并（类似 SQL JOIN）
merged = pd.merge(sales, customers, on="customer_id", how="left")
```

## 数据清洗

```python
# 删除重复行
df = df.drop_duplicates()

# 处理缺失值
df = df.fillna(0)  # 填充为 0
df = df.dropna()   # 删除含缺失值的行

# 去除空格
df["name"] = df["name"].str.strip()

# 类型转换
df["date"] = pd.to_datetime(df["date"])
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
```
