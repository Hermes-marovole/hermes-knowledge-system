# 营养计算公式详解

> 本文档详细说明芽米营养工作站食物营养成分的计算方法和单位转换规则。

---

## 核心计算公式

### 基础公式

```
实际营养值 = (每100g营养值 × 实际重量) / 100
```

### 公式变量

| 变量 | 说明 | 来源 |
|------|------|------|
| 每100g营养值 | API 返回的 elements 值 | type=3 API |
| 实际重量 | 根据单位换算后的克数 | 单位转换表 |
| 实际营养值 | 最终计算结果 | 公式计算 |

---

## 单位转换表

### 标准单位换算

| 原始单位 | 换算系数 | 换算为克 | 示例 |
|----------|----------|----------|------|
| g | 1 | 直接使用 | 35g = 35g |
| 盒 | 250 | × 250 | 1盒 = 250g |
| 杯 | 200 | × 200 | 1杯 = 200g |
| 个 | 100 | × 100 | 1个鸡蛋 ≈ 50g |
| 只 | 100 | × 100 | 1只虾 ≈ 10g |
| 把 | 50 | × 50 | 1把青菜 ≈ 100g |
| 勺 | 15 | × 15 | 1勺油 ≈ 10g |
| 碗 | 300 | × 300 | 1碗米饭 ≈ 150g |
| 片 | 5 | × 5 | 1片面包 ≈ 30g |
| 粒 | 2 | × 2 | 1粒米 ≈ 0.02g |

### 液体单位换算

| 原始单位 | 换算系数 | 说明 |
|----------|----------|------|
| ml | 1 | 1ml ≈ 1g (水/牛奶等) |
| L | 1000 | 1L = 1000g |
| 勺(汤) | 15 | 约15ml |
| 杯(标准) | 240 | 约240ml |

---

## 营养成分计算示例

### 示例1：牛奶营养计算

**输入数据**：
- 食物：牛奶
- 分量：1盒
- API返回每100g营养：热量54kcal, 蛋白质3g, 碳水4.8g, 脂肪3.2g

**计算过程**：
```
实际重量 = 1盒 × 250g/盒 = 250g

热量 = 54 × 250 / 100 = 135 kcal
蛋白质 = 3 × 250 / 100 = 7.5 g
碳水化合物 = 4.8 × 250 / 100 = 12 g
脂肪 = 3.2 × 250 / 100 = 8 g
```

### 示例2：燕麦片营养计算

**输入数据**：
- 食物：燕麦片
- 分量：35g
- API返回每100g营养：热量377kcal, 蛋白质12g, 碳水62g, 脂肪7g

**计算过程**：
```
实际重量 = 35g (直接使用)

热量 = 377 × 35 / 100 = 131.95 ≈ 132 kcal
蛋白质 = 12 × 35 / 100 = 4.2 g
碳水化合物 = 62 × 35 / 100 = 21.7 g
脂肪 = 7 × 35 / 100 = 2.45 ≈ 2.5 g
```

### 示例3：鸡蛋营养计算

**输入数据**：
- 食物：鸡蛋
- 分量：1个
- API返回每100g营养：热量143kcal, 蛋白质12.5g, 碳水1.4g, 脂肪9.5g

**计算过程**：
```
实际重量 = 1个 × 50g/个 = 50g (鸡蛋通常1个约50g)

热量 = 143 × 50 / 100 = 71.5 ≈ 72 kcal
蛋白质 = 12.5 × 50 / 100 = 6.25 ≈ 6.3 g
碳水化合物 = 1.4 × 50 / 100 = 0.7 g
脂肪 = 9.5 × 50 / 100 = 4.75 ≈ 4.8 g
```

---

## Python 实现代码

### 单位转换函数

```python
def unit_to_grams(value: float, unit: str) -> float:
    """
    将各种单位转换为克
    
    Args:
        value: 数量
        unit: 单位名称
    
    Returns:
        对应的克数
    """
    unit_map = {
        'g': 1,
        '克': 1,
        '盒': 250,
        '杯': 200,
        '个': 50,  # 鸡蛋等
        '只': 10,  # 虾等
        '把': 100, # 青菜等
        '勺': 10,  # 油等
        '碗': 150, # 米饭等
        '片': 30,  # 面包等
        'ml': 1,   # 液体
        'l': 1000,
    }
    
    coefficient = unit_map.get(unit, 1)
    return value * coefficient
```

### 营养计算函数

```python
def calculate_nutrition(elements: list, weight_in_grams: float) -> dict:
    """
    根据API返回的elements和实际重量计算营养
    
    Args:
        elements: API返回的elements数组
        weight_in_grams: 实际重量(g)
    
    Returns:
        计算后的营养成分字典
    """
    result = {}
    
    for elem in elements:
        name = elem['name']
        value_per_100g = float(elem['value'])
        
        # 计算实际值
        actual_value = value_per_100g * weight_in_grams / 100
        result[name] = round(actual_value, 2)
    
    return result
```

### 完整计算流程

```python
def calculate_food_nutrition(food_name: str, quantity: float, unit: str) -> dict:
    """
    计算指定食物的营养
    
    Args:
        food_name: 食物名称
        quantity: 数量
        unit: 单位
    
    Returns:
        营养成分字典
    """
    import requests
    
    # 1. 搜索食物获取营养数据
    url = f"https://food.chestnutmates.com/proxy.get/food/web/search?type=3&keyword={food_name}&page=1"
    resp = requests.get(url).json()
    
    if not resp['data']['search_result']:
        return None
    
    food_data = resp['data']['search_result'][0]
    elements = food_data['elements']
    
    # 2. 转换重量
    weight = unit_to_grams(quantity, unit)
    
    # 3. 计算营养
    nutrition = calculate_nutrition(elements, weight)
    
    return {
        '食物': food_name,
        '分量': f"{quantity}{unit}",
        '实际重量(g)': weight,
        '营养': nutrition
    }

# 使用示例
result = calculate_food_nutrition("牛奶", 1, "盒")
print(result)
# 输出: {'食物': '牛奶', '分量': '1盒', '实际重量(g)': 250, '营养': {'热量(kcal)': 135.0, '蛋白质(g)': 7.5, ...}}
```

---

## 食谱总营养计算

### 计算逻辑

```
食谱总营养 = Σ(每餐营养)
每餐营养 = Σ(每种食物营养)
每种食物营养 = 单位转换 → API查询 → 按重量计算
```

### 餐次分类

| 餐次 | 常见时间段 | 典型食物 |
|------|-----------|----------|
| 早餐 | 7:00-9:00 | 牛奶、鸡蛋、面包、粥 |
| 加餐1 | 10:00 | 水果、坚果 |
| 午餐 | 12:00-13:00 | 主食、肉类、蔬菜 |
| 加餐2 | 15:00-16:00 | 酸奶、水果 |
| 晚餐 | 18:00-19:00 | 主食、肉类、蔬菜 |

### Python 实现

```python
def calculate_recipe_nutrition(recipe_detail: dict) -> dict:
    """
    计算整个食谱的总营养
    
    Args:
        recipe_detail: 食谱详情API返回的数据
    
    Returns:
        包含总营养和每餐营养的字典
    """
    total_nutrition = {
        '总重量(g)': 0,
        '热量(kcal)': 0,
        '蛋白质(g)': 0,
        '碳水化合物(g)': 0,
        '脂肪(g)': 0,
        '总膳食纤维(g)': 0
    }
    
    meal_nutrition = {}
    
    for day in recipe_detail['data']['days']:
        day_num = day['day']
        
        for meal in day['meals']:
            meal_type = meal['meal_type']
            meal_key = f"第{day_num}天-{meal_type}"
            meal_nutrition[meal_key] = {
                '热量(kcal)': 0,
                '蛋白质(g)': 0,
                '碳水化合物(g)': 0,
                '脂肪(g)': 0
            }
            
            for food in meal['foods']:
                # 获取食物营养
                food_nutrition = calculate_food_nutrition(
                    food['name'],
                    food['value'],
                    food['unit']
                )
                
                if food_nutrition:
                    # 累加到餐次
                    for key in ['热量(kcal)', '蛋白质(g)', '碳水化合物(g)', '脂肪(g)']:
                        if key in food_nutrition['营养']:
                            meal_nutrition[meal_key][key] += food_nutrition['营养'][key]
                    
                    # 累加到总营养
                    for key in total_nutrition.keys():
                        if key in food_nutrition['营养']:
                            total_nutrition[key] += food_nutrition['营养'][key]
    
    return {
        '总营养': {k: round(v, 2) for k, v in total_nutrition.items()},
        '每餐营养': meal_nutrition
    }
```

---

## 营养参考值

### 每日推荐摄入量 (成人)

| 营养素 | 推荐值 | 单位 |
|--------|--------|------|
| 热量 | 2000-2500 | kcal |
| 蛋白质 | 50-65 | g |
| 碳水化合物 | 250-300 | g |
| 脂肪 | 50-70 | g |
| 膳食纤维 | 25-30 | g |

### 营养素热量系数

| 营养素 | 热量系数 |
|--------|----------|
| 蛋白质 | 4 kcal/g |
| 碳水化合物 | 4 kcal/g |
| 脂肪 | 9 kcal/g |
| 膳食纤维 | 2 kcal/g |

---

## 常见问题

### Q1: API返回的数据准确吗？

A: API返回的是每100g食物的营养成分，数据来源于芽米营养数据库，一般认为是可靠的。但注意：
- 不同品牌/产地可能有差异
- 烹饪方式会影响营养
- 建议作为参考值使用

### Q2: 如何处理找不到的食物？

A: 搜索可能返回近似结果，建议：
1. 尝试使用更通用的名称（如"苹果"而非"红富士"）
2. 检查返回结果的食物名称是否匹配
3. 对不确定的食物标记为"估算值"

### Q3: 计算结果有小数误差？

A: 由于浮点数计算和四舍五入，可能出现0.01级别的误差，这是正常的。建议在最终展示时统一保留1-2位小数。

---

*文档版本：v2.0.0 | 更新日期：2025-04-23*
