# LLM-Wiki Schema: 营养学领域 (Nutrition)

## 领域定义

**领域**: 营养学 (Nutrition Science)
**版本**: 0.1.0
**创建日期**: 2026-04-24

---

## 核心实体类型 (Entity Types)

### 1. 益生菌 (Probiotics)
| 属性 | 类型 | 描述 |
|------|------|------|
| name | string | 益生菌名称 |
| strain | string | 菌株编号 |
| genus | string | 属 |
| species | string | 种 |
| benefits | array | 健康益处 |
| research_level | enum | 研究成熟度: preliminary/ongoing/established |

**重点实体**: AKK益生菌 (Akkermansia muciniphila)

### 2. 矿物质补充剂 (Mineral Supplements)
| 属性 | 类型 | 描述 |
|------|------|------|
| name | string | 补充剂名称 |
| chemical_form | string | 化学形态 |
| bioavailability | float | 生物利用率 (0-1) |
| recommended_dose | object | 推荐剂量 |
| deficiency_symptoms | array | 缺乏症状 |
| food_sources | array | 食物来源 |

**重点实体**: 镁补充剂 (Magnesium)

### 3. 健康状况 (Health Conditions)
| 属性 | 类型 | 描述 |
|------|------|------|
| name | string | 健康状况名称 |
| category | enum | 类别: metabolic/digestive/cardiovascular |
| related_nutrients | array | 相关营养素 |
| risk_factors | array | 风险因素 |

**重点实体**: 肠道健康 (Gut Health)

### 4. 营养保健品 (Nutraceuticals)
| 属性 | 类型 | 描述 |
|------|------|------|
| name | string | 产品名称 |
| category | enum | 类别: supplement/functional_food/botanical |
| active_ingredients | array | 活性成分 |
| claims | array | 功效声明 |
| evidence_level | enum | 证据等级: weak/moderate/strong |

---

## 概念类型 (Concept Types)

### 1. 作用机制 (Mechanisms)
- 肠道屏障功能
- 菌群-肠-脑轴
- 炎症调节

### 2. 研究方法 (Research Methods)
- 随机对照试验 (RCT)
- 元分析 (Meta-analysis)
- 队列研究

### 3. 评估指标 (Metrics)
- 肠道通透性
- 炎症标志物 (CRP, IL-6)
- 菌群多样性指数

---

## 比较类型 (Comparison Types)

### 1. 产品比较
- 不同品牌镁补充剂对比
- 益生菌菌株功效对比

### 2. 干预比较
- 饮食 vs 补充剂
- 单一 vs 复合配方

### 3. 证据比较
- 研究质量评估矩阵
- 证据冲突分析

---

## 关系定义 (Relations)

```
entity:probiotic --[improves]--> entity:health_condition
entity:supplement --[treats]--> entity:deficiency
entity:nutraceutical --[contains]--> entity:compound
concept:mechanism --[explains]--> entity:probiotic
comparison:product --[evaluates]--> entity:supplement
```

---

## 文件命名规范

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| 实体 | `{type}_{kebab-name}.md` | `probiotic_akkermansia.md` |
| 概念 | `concept_{kebab-name}.md` | `concept_gut-barrier.md` |
| 比较 | `compare_{kebab-names}.md` | `compare_magnesium-forms.md` |

---

## 状态标记

- 🟢 **verified**: 多源验证
- 🟡 **draft**: 待验证
- 🔴 **disputed**: 存在争议
- ⚪ **stub**: 待扩展
