# 批量处理与断点续传指南

> 本文档详细说明如何批量抓取芽米营养工作站的全部食谱数据，包含进度管理、错误处理和性能优化。

---

## 批量抓取架构

```
┌──────────────────────────────────────────────────────────────┐
│                     批量抓取流程                               │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  1. 获取食谱列表                                                │
│     └── 调用 type=2 API，遍历14页获取全部272个食谱token          │
│                                                                │
│  2. 批量获取详情                                                │
│     └── 对每个token调用详情API获取每日餐单                       │
│                                                                │
│  3. 营养分析计算                                                │
│     └── 对每个食物的type=3搜索获取营养并计算                     │
│                                                                │
│  4. 进度保存                                                    │
│     └── 每10个食谱保存一次进度到 progress.json                 │
│                                                                │
│  5. 输出结果                                                    │
│     └── 生成 JSON + Markdown 双格式                            │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## 核心脚本

### 完整批量抓取脚本

```python
#!/usr/bin/env python3
"""
批量抓取芽米营养工作站食谱数据
支持断点续传、进度保存、错误重试
"""

import requests
import json
import time
import os
from pathlib import Path
from datetime import datetime

class ChestnutmatesBatchScraper:
    def __init__(self, delay=0.3, progress_file="progress.json"):
        self.base_url = "https://food.chestnutmates.com/proxy.get/food/web"
        self.delay = delay
        self.progress_file = progress_file
        self.session = requests.Session()
        
        # 加载进度
        self.processed_tokens = self._load_progress()
        self.results = []
        
    def _load_progress(self):
        """加载已处理的token列表"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                print(f"✅ 已加载进度: {len(data)} 个食谱已处理")
                return set(data.keys())
        return set()
    
    def _save_progress(self, token, data):
        """保存处理进度"""
        existing = {}
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                existing = json.load(f)
        
        existing[token] = {
            'processed_at': datetime.now().isoformat(),
            'name': data.get('name', 'unknown')
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    
    def _api_call(self, url, max_retries=3):
        """带重试的API调用"""
        for i in range(max_retries):
            try:
                resp = self.session.get(url, timeout=30)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    wait = 2 ** i
                    print(f"  ⚠️  请求频繁，等待{wait}秒...")
                    time.sleep(wait)
                else:
                    resp.raise_for_status()
            except Exception as e:
                if i == max_retries - 1:
                    print(f"  ❌ 请求失败: {e}")
                    return None
                time.sleep(1)
        return None
    
    def get_all_recipes(self):
        """获取全部272个食谱列表"""
        all_recipes = []
        
        for page in range(1, 15):  # 共14页
            url = f"{self.base_url}/search?type=2&keyword=&page={page}"
            data = self._api_call(url)
            
            if data and data.get('data', {}).get('search_result'):
                recipes = data['data']['search_result']
                all_recipes.extend(recipes)
                print(f"📄 第{page}页: 获取 {len(recipes)} 个食谱")
            else:
                print(f"⚠️ 第{page}页: 获取失败")
            
            time.sleep(self.delay)
        
        print(f"\n✅ 总计: {len(all_recipes)} 个食谱")
        return all_recipes
    
    def get_recipe_detail(self, token):
        """获取单个食谱详情"""
        url = f"{self.base_url}/cookbook?token={token}"
        return self._api_call(url)
    
    def get_food_nutrition(self, food_name):
        """获取食物营养成分"""
        url = f"{self.base_url}/search?type=3&keyword={food_name}&page=1"
        return self._api_call(url)
    
    def calculate_nutrition(self, elements, weight_grams):
        """计算实际营养值"""
        result = {}
        for elem in elements:
            name = elem['name']
            value_per_100g = float(elem['value'])
            actual = value_per_100g * weight_grams / 100
            result[name] = round(actual, 2)
        return result
    
    def unit_to_grams(self, value, unit):
        """单位转换"""
        unit_map = {
            'g': 1, '克': 1,
            '盒': 250, '杯': 200,
            '个': 50, '只': 10,
            '把': 100, '勺': 10,
            '碗': 150, '片': 30,
        }
        return value * unit_map.get(unit, 1)
    
    def process_recipe(self, recipe_basic):
        """处理单个食谱"""
        token = recipe_basic['token']
        
        # 检查是否已处理
        if token in self.processed_tokens:
            print(f"  ⏭️  跳过 (已处理): {recipe_basic['name']}")
            return None
        
        print(f"\n🍽️  处理: {recipe_basic['name']}")
        
        # 获取详情
        detail = self.get_recipe_detail(token)
        if not detail:
            print(f"  ❌ 获取详情失败")
            return None
        
        time.sleep(self.delay)
        
        # 构建结果
        result = {
            'token': token,
            'name': recipe_basic['name'],
            'author': recipe_basic.get('author', '未知'),
            'heat': recipe_basic.get('heat', ''),
            'label': recipe_basic.get('label', []),
            'days': [],
            'total_nutrition': {
                '总重量(g)': 0, '热量(kcal)': 0,
                '蛋白质(g)': 0, '碳水化合物(g)': 0,
                '脂肪(g)': 0, '总膳食纤维(g)': 0
            },
            'foods_detail': []
        }
        
        # 处理每一天
        for day_data in detail.get('data', {}).get('days', []):
            day_result = {
                'day': day_data['day'],
                'meals': []
            }
            
            for meal in day_data.get('meals', []):
                meal_result = {
                    'meal_type': meal['meal_type'],
                    'foods': []
                }
                
                for food in meal.get('foods', []):
                    # 获取食物营养
                    nutrition_data = self.get_food_nutrition(food['name'])
                    time.sleep(self.delay)
                    
                    if nutrition_data and nutrition_data.get('data', {}).get('search_result'):
                        food_info = nutrition_data['data']['search_result'][0]
                        elements = food_info.get('elements', [])
                        
                        # 计算营养
                        weight = self.unit_to_grams(food['value'], food['unit'])
                        nutrition = self.calculate_nutrition(elements, weight)
                        
                        food_detail = {
                            'name': food['name'],
                            'quantity': f"{food['value']}{food['unit']}",
                            'weight_g': weight,
                            'nutrition': nutrition
                        }
                        
                        meal_result['foods'].append(food_detail)
                        
                        # 累加总营养
                        for key in result['total_nutrition'].keys():
                            if key in nutrition:
                                result['total_nutrition'][key] += nutrition[key]
                
                day_result['meals'].append(meal_result)
            
            result['days'].append(day_result)
        
        # 保存进度
        self._save_progress(token, result)
        self.processed_tokens.add(token)
        
        print(f"  ✅ 完成: {recipe_basic['name']}")
        return result
    
    def run(self, limit=None):
        """执行批量抓取"""
        print("=" * 50)
        print("🚀 开始批量抓取芽米营养工作站食谱")
        print("=" * 50)
        
        # 获取所有食谱
        recipes = self.get_all_recipes()
        if limit:
            recipes = recipes[:limit]
        
        # 处理每个食谱
        for i, recipe in enumerate(recipes):
            result = self.process_recipe(recipe)
            if result:
                self.results.append(result)
            
            # 每10个保存一次完整结果
            if (i + 1) % 10 == 0:
                self._save_full_results()
                progress = len(self.processed_tokens) / len(recipes) * 100
                print(f"\n📊 进度: {len(self.processed_tokens)}/{len(recipes)} ({progress:.1f}%)")
        
        # 最终保存
        self._save_full_results()
        print("\n✅ 批量抓取完成!")
        return self.results
    
    def _save_full_results(self):
        """保存完整结果到文件"""
        with open('all_recipes_nutrition.json', 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"  💾 已保存 {len(self.results)} 个食谱到 all_recipes_nutrition.json")


# 运行脚本
if __name__ == "__main__":
    scraper = ChestnutmatesBatchScraper(delay=0.3)
    
    # 可以设置 limit 参数测试少量数据
    # scraper.run(limit=5)
    
    # 完整运行
    scraper.run()
```

---

## 进度监控

### 实时监控脚本

```python
#!/usr/bin/env python3
"""
进度监控脚本 - 每5分钟报告一次进度
"""

import json
import time
import os
from datetime import datetime

def monitor_progress(interval=300, progress_file="progress.json"):
    """
    监控批量抓取进度
    
    Args:
        interval: 报告间隔（秒），默认5分钟
        progress_file: 进度文件路径
    """
    total = 272
    
    print(f"📊 开始监控进度 (每{interval//60}分钟报告一次)")
    print("按 Ctrl+C 停止监控\n")
    
    try:
        while True:
            if os.path.exists(progress_file):
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                
                processed = len(data)
                percentage = processed / total * 100
                remaining = total - processed
                
                # 估算剩余时间 (假设每个食谱平均30秒)
                avg_time_per_recipe = 30  # 秒
                remaining_time = remaining * avg_time_per_recipe
                hours = remaining_time // 3600
                minutes = (remaining_time % 3600) // 60
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}]")
                print(f"  已处理: {processed}/{total} ({percentage:.1f}%)")
                print(f"  剩余: {remaining} 个食谱")
                print(f"  预计剩余时间: {hours}小时{minutes}分钟")
                print()
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 等待进度文件...")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n✋ 监控已停止")

if __name__ == "__main__":
    monitor_progress()
```

### 后台运行监控

```bash
# 在后台运行批量抓取
python batch_scraper.py &
SCRAPER_PID=$!

# 在另一个终端运行监控
python monitor_progress.py

# 如果需要停止批量抓取
kill $SCRAPER_PID
```

---

## 断点续传机制

### 原理

```
┌─────────────────────────────────────────────────────────────┐
│                    断点续传机制                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  progress.json 结构:                                         │
│  {                                                           │
│    "token_xxx": {                                            │
│      "processed_at": "2025-04-23T10:30:00",                 │
│      "name": "7天减脂食谱"                                   │
│    },                                                        │
│    "token_yyy": { ... }                                      │
│  }                                                           │
│                                                              │
│  启动时:                                                     │
│  1. 读取 progress.json                                       │
│  2. 提取所有已处理的 token                                   │
│  3. 跳过这些 token，继续处理剩余                             │
│                                                              │
│  处理时:                                                     │
│  1. 每完成一个食谱，立即写入 progress.json                   │
│  2. 每10个食谱保存完整结果到 all_recipes_nutrition.json      │
│                                                              │
│  中断恢复:                                                   │
│  1. 重新运行脚本                                             │
│  2. 自动检测已处理的 token                                   │
│  3. 从断点继续                                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 性能优化

### 1. 异步请求

```python
import asyncio
import aiohttp
import aiofiles

async def async_batch_scrape(recipes, delay=0.3):
    """异步批量抓取"""
    results = []
    
    async with aiohttp.ClientSession() as session:
        for recipe in recipes:
            async with session.get(
                f"https://food.chestnutmates.com/proxy.get/food/web/cookbook",
                params={'token': recipe['token']}
            ) as resp:
                data = await resp.json()
                results.append(data)
            
            await asyncio.sleep(delay)
    
    return results

# 运行
asyncio.run(async_batch_scrape(recipes))
```

### 2. 并发控制

```python
import asyncio
import aiohttp
from asyncio import Semaphore

async def controlled_concurrent_scrape(recipes, max_concurrent=5, delay=0.3):
    """带并发控制的批量抓取"""
    semaphore = Semaphore(max_concurrent)
    results = []
    
    async def fetch_one(recipe):
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                url = f"https://food.chestnutmates.com/proxy.get/food/web/cookbook"
                async with session.get(url, params={'token': recipe['token']}) as resp:
                    data = await resp.json()
                    await asyncio.sleep(delay)
                    return data
    
    tasks = [fetch_one(r) for r in recipes]
    results = await asyncio.gather(*tasks)
    return results
```

### 3. 请求频率对比

| 策略 | 并发数 | 延迟 | 272个食谱耗时 | 风险 |
|------|--------|------|--------------|------|
| 串行 | 1 | 0.3s | ~2小时 | 低 |
| 串行 | 1 | 0.15s | ~1小时 | 中 |
| 异步 | 5 | 0.3s | ~25分钟 | 中 |
| 异步 | 10 | 0.3s | ~15分钟 | 高 |

**推荐**：串行 0.3s 延迟，稳定可靠。

---

## 错误处理

### 常见错误与处理

```python
class BatchScraperErrorHandler:
    def handle_error(self, error, context):
        """统一错误处理"""
        error_type = type(error).__name__
        
        handlers = {
            'ConnectionError': self._handle_connection_error,
            'TimeoutError': self._handle_timeout,
            'HTTPError': self._handle_http_error,
            'JSONDecodeError': self._handle_json_error,
        }
        
        handler = handlers.get(error_type, self._handle_unknown)
        return handler(error, context)
    
    def _handle_connection_error(self, error, context):
        """连接错误 - 等待后重试"""
        print(f"  🔌 连接错误: {error}")
        time.sleep(5)
        return 'retry'
    
    def _handle_timeout(self, error, context):
        """超时 - 延长超时时间重试"""
        print(f"  ⏱️  超时: {error}")
        return 'retry_with_longer_timeout'
    
    def _handle_http_error(self, error, context):
        """HTTP错误 - 根据状态码处理"""
        if error.response.status_code == 429:
            print(f"  🚫 请求过于频繁，等待60秒...")
            time.sleep(60)
            return 'retry'
        elif error.response.status_code == 500:
            print(f"  🔥 服务器错误，跳过此项目")
            return 'skip'
        else:
            return 'retry'
    
    def _handle_json_error(self, error, context):
        """JSON解析错误 - 记录原始响应"""
        print(f"  📄 JSON解析错误")
        with open(f'error_response_{context["token"]}.txt', 'w') as f:
            f.write(context.get('raw_response', ''))
        return 'skip'
    
    def _handle_unknown(self, error, context):
        """未知错误 - 记录并跳过"""
        print(f"  ❓ 未知错误: {error}")
        return 'skip'
```

---

## 输出文件管理

### 目录结构

```
output/
├── all_recipes_nutrition.json      # 完整JSON数据
├── progress.json                   # 进度跟踪
├── errors.log                      # 错误日志
├── categorized/                    # 按分类整理
│   ├── 减脂瘦身/
│   │   ├── 7天减脂食谱.md
│   │   └── README.md
│   ├── 疾病管理/
│   ├── 孕期产后/
│   ├── 儿童营养/
│   ├── 增肌健身/
│   └── 其他/
└── by_date/                        # 按日期备份
    ├── 2025-04-23/
    ├── 2025-04-22/
    └── ...
```

---

## 运行建议

### 第一次运行

```bash
# 1. 测试少量数据 (前5个食谱)
python -c "
from batch_scraper import ChestnutmatesBatchScraper
scraper = ChestnutmatesBatchScraper(delay=0.3)
scraper.run(limit=5)
"

# 2. 检查输出格式是否正确
ls -la all_recipes_nutrition.json progress.json

# 3. 确认无误后全量运行
python batch_scraper.py
```

### 日常更新

```bash
# 增量更新 (只处理新增加的食谱)
python batch_scraper.py --incremental

# 强制重新抓取全部
python batch_scraper.py --force
```

### 定时任务

```bash
# crontab -e
# 每周日凌晨2点更新数据
0 2 * * 0 cd /path/to/project && python batch_scraper.py
```

---

*文档版本：v2.0.0 | 更新日期：2025-04-23*
