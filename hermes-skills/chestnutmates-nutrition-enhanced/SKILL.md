---
name: chestnutmates-nutrition-enhanced
description: "抓取芽米医学营养工作站(chestnutmates.com)的食谱和营养分析数据 —— 支持批量抓取、营养计算、分类输出"
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [nutrition, api, scraping, food, chestnutmates, recipe, health]
    category: research
    related_skills: [authenticated-site-scraping, chrome-cdp-mac-scraping, llm-wiki]
    linked_files:
      - references/api-endpoints.md
      - references/nutrition-calculation.md
      - references/batch-processing.md
      - templates/output-formats.md
      - scripts/example-code.py
---

# 芽米医学营养工作站数据抓取 (增强版)

> 快速导航：
> - [5秒速览](#5秒速览) → 了解核心功能
> - [快速开始](#快速开始) → 5分钟上手
> - [完整 API 文档](references/api-endpoints.md) → 所有端点详解
> - [营养计算公式](references/nutrition-calculation.md) → 单位转换与计算
> - [批量处理指南](references/batch-processing.md) → 大规模数据处理

---

## 5秒速览

| 功能 | 描述 | 难度 |
|------|------|------|
| **食谱抓取** | 抓取272个公开食谱的基础信息 | ⭐ |
| **营养分析** | 通过 API 计算食物热量、蛋白质、碳水、脂肪 | ⭐⭐ |
| **批量导出** | 生成 JSON + Markdown 双格式输出 | ⭐⭐ |
| **分类整理** | 按减脂/疾病管理/孕期/儿童等自动分类 | ⭐ |

**核心 API**：`food.chestnutmates.com/proxy.get/food/web/search?type={2\|3}`

---

## 快速开始

### 1. 单次查询食物营养

```python
import requests

food_name = "牛奶"
url = f"https://food.chestnutmates.com/proxy.get/food/web/search?type=3&keyword={food_name}&page=1"
data = requests.get(url).json()

if data['data']['search_result']:
    elements = data['data']['search_result'][0]['elements']
    for elem in elements:
        print(f"{elem['name']}: {elem['value']}")
```

### 2. 抓取单个食谱详情

```python
# 获取食谱列表
token = "xxx"  # 从搜索 API 获取
detail_url = f"https://food.chestnutmates.com/proxy.get/food/web/cookbook?token={token}"
detail = requests.get(detail_url).json()
```

### 3. 批量抓取全部食谱

见 [批量处理指南](references/batch-processing.md) 获取完整脚本和断点续传方案。

---

## 数据抓取架构

```
┌─────────────────────────────────────────────────────────────┐
│                    芽米营养工作站 API                          │
├─────────────────────────────────────────────────────────────┤
│  公开 API (无需登录)                                          │
│  ├── type=2 → 272个食谱基础信息                              │
│  ├── type=3 → 食物营养成分 (热量/蛋白质/碳水/脂肪/膳食纤维)    │
│  └── type=6 → 菜谱详情                                       │
├─────────────────────────────────────────────────────────────┤
│  认证 API (需登录) - 当前 Skill 暂不支持                      │
│  ├── 食材分类统计 (谷薯/蔬菜/水果/肉蛋奶等)                    │
│  ├── 维生素详情 (A/B/C/D/E等)                                │
│  └── 矿物质详情 (钙/铁/锌/硒等)                              │
└─────────────────────────────────────────────────────────────┘
```

---

## API 类型速查表

| type | 用途 | 返回字段 | 营养数据 |
|------|------|----------|----------|
| **2** | 食谱搜索 | token, name, heat, label, author | ❌ |
| **3** | 食物/菜谱搜索 | elements, name, images | ✅ 热量/蛋白质/碳水/脂肪/纤维 |
| **6** | 菜谱详情 | 完整菜谱信息 | ✅ |

---

## 营养分析计算方法

### 单位转换表

| 单位 | 换算为克 |
|------|----------|
| g | 直接使用 |
| 盒 | 250g |
| 杯 | 200g |
| 个/只 | 100g |
| 把 | 50g |
| 勺 | 15g |
| 碗 | 300g |

### 计算公式

```
实际营养值 = (每100g营养值 × 实际重量) / 100
```

详细计算公式和单位转换见 [营养计算公式](references/nutrition-calculation.md)。

---

## 输出格式

### JSON 格式（完整数据）

```json
{
  "食谱": "食谱名称",
  "作者": "作者名",
  "天数": 7,
  "总营养": {
    "总重量(g)": 1500,
    "热量(kcal)": 1400,
    "蛋白质(g)": 70,
    "碳水化合物(g)": 180,
    "脂肪(g)": 45,
    "总膳食纤维(g)": 25
  },
  "食物详情": [
    {"食物": "牛奶", "分量": "1盒", "营养": {...}}
  ]
}
```

### Markdown 格式（按餐单）

```markdown
# 食谱名称

**作者：** 作者名  
**天数：** 7 天

---

## 第1天

**早餐：**
- 牛奶 1盒
- 燕麦片 35g

**午餐：**
- 杂粮饭 100g
- 黄瓜炒鸡蛋 150g
```

更多输出模板见 [输出格式模板](templates/output-formats.md)。

---

## 食谱分类规则

| 类别 | 关键词匹配 |
|------|-----------|
| **减脂瘦身** | 减脂、减重、减肥、瘦身、体重控制 |
| **疾病管理** | 糖尿病、痛风、脂肪肝、高血压、冠心病、肾病、贫血、癌症 |
| **孕期产后** | 孕期、产后、妊娠、哺乳 |
| **儿童营养** | 儿童、宝宝、幼儿 |
| **增肌健身** | 增肌、健身、高蛋白 |
| **其他** | 不属于以上类别 |

---

## 项目文件结构

```
chestnutmates-nutrition-enhanced/
├── SKILL.md                          # 主文件（本文件）
├── references/
│   ├── api-endpoints.md              # 完整 API 端点文档
│   ├── nutrition-calculation.md      # 营养计算详细说明
│   └── batch-processing.md           # 批量处理与断点续传
├── templates/
│   ├── output-formats.md             # 输出格式模板
│   ├── recipe-markdown-template.md   # 食谱 Markdown 模板
│   └── index-template.md             # 索引文件模板
└── scripts/
    ├── example-code.py               # 示例代码
    ├── batch-scraper.py              # 批量抓取脚本
    └── nutrition-calculator.py       # 营养计算器
```

---

## 完整数据示例

### 食谱详情 (type=2)

```json
{
  "token": "xxx",
  "name": "7天减脂食谱",
  "heat": "1400kcal",
  "label": ["减脂", "低卡"],
  "author": "营养师小王",
  "days": 7
}
```

### 营养成分 (type=3)

```json
{
  "name": "牛奶",
  "elements": [
    {"name": "总重量(g)", "value": "100"},
    {"name": "热量(kcal)", "value": "54"},
    {"name": "蛋白质(g)", "value": "3"},
    {"name": "碳水化合物(g)", "value": "4.8"},
    {"name": "脂肪(g)", "value": "3.2"},
    {"name": "总膳食纤维(g)", "value": "0"}
  ]
}
```

---

## 注意事项与最佳实践

### ⚠️ 请求频率控制

| 场景 | 建议间隔 | 说明 |
|------|----------|------|
| 单次查询 | 0.15s | 基础延迟 |
| 批量抓取 | 0.3s | 避免触发限制 |
| 大量数据 | 0.5s | 272个食谱约需2小时 |

### ⚠️ 搜索匹配问题

- type=3 搜索可能返回最相关结果，不一定是精确匹配
- 部分特殊食品（保健品、定制食品）可能无数据
- 建议对返回结果进行二次验证

### ⚠️ 常见错误

```python
# ❌ 错误：f-string 中包含反斜杠
filename = f"{name.replace('/', '_').replace('\\', '_')}.md"

# ✅ 正确：先赋值给变量
safe_name = name.replace('/', '_').replace('\\', '_')
filename = f"{safe_name}.md"
```

### ✅ 最佳实践

1. **断点续传**：每10个食谱保存一次进度
2. **双格式输出**：同时保存 JSON（完整数据）和 Markdown（可读性）
3. **分类存储**：按类别分文件夹，方便浏览
4. **进度监控**：使用后台进程 + 定期报告

---

## 认证数据说明

> ⚠️ 完整的营养分析（维生素、矿物质、食材分类统计）需要登录态才能获取。
> 本 Skill 专注于公开 API 的数据抓取，认证数据获取需结合 `authenticated-site-scraping` skill。

| 数据类型 | 公开 API | 认证 API |
|----------|----------|----------|
| 热量 | ✅ | ✅ |
| 蛋白质/碳水/脂肪 | ✅ | ✅ |
| 膳食纤维 | ✅ | ✅ |
| 食材分类统计 | ❌ | ✅ |
| 维生素 | ❌ | ✅ |
| 矿物质 | ❌ | ✅ |

---

## 相关 Skill 联动

| Skill | 用途 |
|-------|------|
| [authenticated-site-scraping](../authenticated-site-scraping/SKILL.md) | 获取需要登录的完整营养数据 |
| [chrome-cdp-mac-scraping](../chrome-cdp-mac-scraping/SKILL.md) | 浏览器自动化抓取 |
| [llm-wiki](../llm-wiki/SKILL.md) | 将抓取的数据构建为知识库 |

---

## 更新日志

### v2.0.0 (2025-04-23)
- ✅ 重构为渐进式披露结构
- ✅ 添加完整 YAML front-matter
- ✅ 创建 linked_files 目录结构
- ✅ 分离详细文档到 references/
- ✅ 添加输出格式模板
- ✅ 补充完整示例代码

### v1.0.0 (原始版本)
- 基础 API 文档
- 单次查询示例
- 基础分类规则

---

*本 Skill 为 chestnutmates-nutrition 的增强版本，基于 ai-agent-knowledge-systems 最佳实践重构。*
