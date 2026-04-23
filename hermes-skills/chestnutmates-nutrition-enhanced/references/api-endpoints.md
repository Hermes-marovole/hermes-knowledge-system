# 芽米营养工作站 API 端点详解

> 本文档包含 chestnutmates-nutrition-enhanced skill 使用的所有 API 端点完整说明。

---

## 基础信息

| 属性 | 值 |
|------|-----|
| 基础 URL | `https://food.chestnutmates.com` |
| 协议 | HTTPS |
| 认证 | 公开 API 无需认证，完整数据需登录态 |
| 数据格式 | JSON |

---

## 端点列表

### 1. 食谱搜索 API

**端点**：`GET /proxy.get/food/web/search`

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | int | ✅ | 2=食谱, 3=食物/菜谱, 6=菜谱 |
| keyword | string | ❌ | 搜索关键词 |
| page | int | ❌ | 页码，默认1 |

**请求示例**：
```bash
curl "https://food.chestnutmates.com/proxy.get/food/web/search?type=2&keyword=&page=1"
```

**响应示例** (type=2)：
```json
{
  "code": 200,
  "message": "OK",
  "data": {
    "search_result": [
      {
        "token": "xxx",
        "name": "7天减脂食谱",
        "heat": "1400kcal",
        "label": ["减脂"],
        "author": "营养师小王",
        "created_at": "2024-01-15",
        "image_url": "https://file.chestnutmates.com/images/xxx.png"
      }
    ],
    "total": 272,
    "page": 1,
    "per_page": 20
  }
}
```

---

### 2. 食谱详情 API

**端点**：`GET /proxy.get/food/web/cookbook`

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | ✅ | 食谱唯一标识 |

**请求示例**：
```bash
curl "https://food.chestnutmates.com/proxy.get/food/web/cookbook?token=xxx"
```

**响应示例**：
```json
{
  "code": 200,
  "data": {
    "name": "7天减脂食谱",
    "author": "营养师小王",
    "days": [
      {
        "day": 1,
        "meals": [
          {
            "meal_type": "早餐",
            "foods": [
              {
                "id": 123,
                "name": "牛奶",
                "common_name": "纯牛奶",
                "value": 1,
                "unit": "盒"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

---

### 3. 食物/菜谱搜索 API（营养成分）

**端点**：`GET /proxy.get/food/web/search?type=3`

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | int | ✅ | 固定值 3 |
| keyword | string | ✅ | 食物名称 |
| page | int | ❌ | 页码 |

**请求示例**：
```bash
curl "https://food.chestnutmates.com/proxy.get/food/web/search?type=3&keyword=牛奶&page=1"
```

**响应示例**：
```json
{
  "code": 200,
  "data": {
    "search_result": [
      {
        "id": 456,
        "name": "牛奶",
        "common_name": "纯牛奶",
        "images": ["https://file.chestnutmates.com/images/milk.png"],
        "elements": [
          {"name": "总重量(g)", "value": "100", "unit": "g"},
          {"name": "热量(kcal)", "value": "54", "unit": "kcal"},
          {"name": "蛋白质(g)", "value": "3", "unit": "g"},
          {"name": "碳水化合物(g)", "value": "4.8", "unit": "g"},
          {"name": "脂肪(g)", "value": "3.2", "unit": "g"},
          {"name": "总膳食纤维(g)", "value": "0", "unit": "g"}
        ]
      }
    ]
  }
}
```

**elements 字段说明**：
| 名称 | 说明 | 单位 |
|------|------|------|
| 总重量(g) | 每份重量 | g |
| 热量(kcal) | 卡路里 | kcal |
| 蛋白质(g) | 蛋白质含量 | g |
| 碳水化合物(g) | 碳水含量 | g |
| 脂肪(g) | 脂肪含量 | g |
| 总膳食纤维(g) | 膳食纤维 | g |

---

### 4. 菜谱详情 API (type=6)

**端点**：`GET /proxy.get/food/web/search?type=6`

**用途**：获取菜谱的详细信息，包含制作步骤和完整营养。

**参数**：
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | int | ✅ | 固定值 6 |
| keyword | string | ✅ | 菜谱名称 |
| page | int | ❌ | 页码 |

---

## 错误码说明

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | - |
| 400 | 参数错误 | 检查请求参数 |
| 401 | 未授权 | 需要登录态 |
| 404 | 资源不存在 | 检查 token 或关键词 |
| 429 | 请求过于频繁 | 增加请求间隔 |
| 500 | 服务器错误 | 稍后重试 |

---

## 数据限制

| 限制项 | 值 | 说明 |
|--------|-----|------|
| 食谱总数 | 272个 | type=2 可获取全部 |
| 每页数量 | 20条 | 默认分页大小 |
| 最大页码 | 14页 | 食谱搜索 |
| 搜索延迟 | 建议0.15s+ | 避免触发限流 |

---

## 已弃用/无效端点

以下端点经测试无法获取公开数据：

```
❌ /proxy.get/food/web/cookbook/nutrition?token=xxx
❌ /proxy.get/food/web/cookbook/analysis?token=xxx
❌ /proxy.get/food/web/cookbook/nutrient?token=xxx
❌ /proxy.get/food/web/cookbook/{id}/nutrition
❌ /api/food/cookbook/{id}/nutrition
```

这些端点需要登录态才能访问。

---

## API 调用最佳实践

### 1. 带重试的请求

```python
import requests
import time

def api_call_with_retry(url, max_retries=3):
    for i in range(max_retries):
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 429:
                time.sleep(2 ** i)  # 指数退避
            else:
                resp.raise_for_status()
        except Exception as e:
            if i == max_retries - 1:
                raise
            time.sleep(1)
    return None
```

### 2. 批量请求控制

```python
import asyncio
import aiohttp

async def batch_requests(urls, delay=0.3):
    results = []
    async with aiohttp.ClientSession() as session:
        for url in urls:
            async with session.get(url) as resp:
                results.append(await resp.json())
            await asyncio.sleep(delay)  # 控制频率
    return results
```

---

*文档版本：v2.0.0 | 更新日期：2025-04-23*
