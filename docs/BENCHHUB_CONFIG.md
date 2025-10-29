# BenchHub Configuration Guide

## Overview

This document provides comprehensive information about the BenchHub dataset configuration structure used in BenchhubPlus. The BenchHub dataset follows a structured approach to categorize and filter evaluation questions based on multiple dimensions.

## Configuration Fields

### 1. Problem Type (string)

Defines the format and structure of evaluation questions.

**Valid Values:**
- `Binary`: Yes/No or True/False questions
- `MCQA`: Multiple Choice Questions with Answer options  
- `short-form`: Short answer questions requiring brief responses
- `open-ended`: Long-form, open-ended questions requiring detailed responses

**Example:**
```json
{
  "problem_type": "MCQA"
}
```

### 2. Target Type (string)

Specifies whether questions target universal knowledge or specific cultural/regional knowledge.

**Valid Values:**
- `General`: Universal knowledge questions applicable across cultures
- `Local`: Culture-specific or region-specific questions

**Example:**
```json
{
  "target_type": "General"
}
```

### 3. Subject Type (list)

Hierarchical subject categorization system with 6 coarse-grained categories and 64 fine-grained subcategories.

#### Coarse-Grained Categories (6)

1. **Science**
2. **Technology** 
3. **Humanities and Social Science (HASS)**
4. **Arts & Sports**
5. **Culture**
6. **Social Intelligence**

#### Fine-Grained Subcategories (64)

**Science (15 subcategories):**
- `Math/Algebra`
- `Math/Geometry` 
- `Math/Statistics`
- `Math/Calculus`
- `Physics/Classical Mechanics`
- `Physics/Thermodynamics`
- `Physics/Electromagnetism`
- `Chemistry/General`
- `Chemistry/Organic`
- `Chemistry/Inorganic`
- `Biology/General`
- `Biology/Genetics`
- `Biology/Ecology`
- `Earth Science/Geology`
- `Earth Science/Meteorology`

**Technology (11 subcategories):**
- `Tech./Computer Science`
- `Tech./Electrical Eng.`
- `Tech./Mechanical Eng.`
- `Tech./Civil Eng.`
- `Tech./Chemical Eng.`
- `Tech./Materials Science`
- `Tech./Information Systems`
- `Tech./Robotics`
- `Tech./AI/ML`
- `Tech./Cybersecurity`
- `Tech./Data Science`

**Humanities and Social Science (14 subcategories):**
- `HASS/History`
- `HASS/Philosophy`
- `HASS/Literature`
- `HASS/Linguistics`
- `HASS/Psychology`
- `HASS/Sociology`
- `HASS/Anthropology`
- `HASS/Political Science`
- `HASS/Economics`
- `HASS/Geography`
- `HASS/Education`
- `HASS/Law`
- `HASS/International Relations`
- `HASS/Public Administration`

**Arts & Sports (10 subcategories):**
- `Arts/Visual Arts`
- `Arts/Music`
- `Arts/Theater`
- `Arts/Film`
- `Arts/Design`
- `Arts/Architecture`
- `Sports/General`
- `Sports/Team Sports`
- `Sports/Individual Sports`
- `Sports/Olympic Sports`

**Culture (9 subcategories):**
- `Culture/Korean Traditional`
- `Culture/East Asian`
- `Culture/Western`
- `Culture/World Cultures`
- `Culture/Religion`
- `Culture/Mythology`
- `Culture/Festivals`
- `Culture/Food`
- `Culture/Fashion`

**Social Intelligence (9 subcategories):**
- `Social/Communication`
- `Social/Ethics`
- `Social/Etiquette`
- `Social/Leadership`
- `Social/Teamwork`
- `Social/Conflict Resolution`
- `Social/Emotional Intelligence`
- `Social/Cultural Sensitivity`
- `Social/Professional Skills`

**Example:**
```json
{
  "subject_type": ["Technology", "Tech./Computer Science"]
}
```

### 4. Task Type (string)

Defines the cognitive skill or capability required to solve the problem.

**Valid Values:**
- `Knowledge`: Factual recall and information retrieval
- `Reasoning`: Logical thinking, problem-solving, and inference
- `Value`: Value judgment and ethical reasoning
- `Alignment`: Cultural and social alignment assessment

**Example:**
```json
{
  "task_type": "Knowledge"
}
```

### 5. External Tool Usage (boolean)

Indicates whether external tools or resources are required to solve the problem.

**Valid Values:**
- `true`: Requires calculators, search engines, reference materials, or other external tools
- `false`: Can be solved using internal knowledge and reasoning only

**Example:**
```json
{
  "external_tool_usage": false
}
```

## Complete Configuration Example

Here's a complete BenchHub configuration example:

```json
{
  "problem_type": "MCQA",
  "target_type": "General",
  "subject_type": ["Technology", "Tech./Electrical Eng."],
  "task_type": "Knowledge",
  "external_tool_usage": false
}
```

## Usage in BenchhubPlus

### 1. Plan Configuration

```python
from apps.core.schemas import PlanConfig

plan = PlanConfig(
    problem_type="MCQA",
    target_type="General",
    subject_type=["Science", "Math/Algebra"],
    task_type="Reasoning",
    external_tool_usage=False,
    language="Korean",
    sample_size=100
)
```

### 2. Natural Language Query Processing

The Planner Agent automatically converts natural language queries to BenchHub configurations:

**Input:** "한국어로 된 프로그래밍 문제를 잘 푸는 모델을 찾고 싶어"

**Output:**
```json
{
  "problem_type": "MCQA",
  "target_type": "General", 
  "subject_type": ["Technology", "Tech./Computer Science"],
  "task_type": "Knowledge",
  "external_tool_usage": false,
  "language": "Korean",
  "sample_size": 100
}
```

### 3. HRET Integration

BenchHub configurations are automatically converted to HRET-compatible formats:

```yaml
datasets:
  - name: "benchhub_filtered"
    type: "benchhub"
    filters:
      problem_type: "MCQA"
      target_type: "General"
      subject_type: ["Technology", "Tech./Computer Science"]
      task_type: "Knowledge"
      external_tool_usage: false
      language: "Korean"
```

## Filtering and Querying

### Single Subject Filter
```json
{
  "subject_type": ["Science"]
}
```

### Multi-Subject Filter
```json
{
  "subject_type": ["Science", "Math/Algebra", "Physics/Classical Mechanics"]
}
```

### Complex Filter Combination
```json
{
  "problem_type": "open-ended",
  "target_type": "Local",
  "subject_type": ["Culture", "Culture/Korean Traditional"],
  "task_type": "Value",
  "external_tool_usage": false
}
```

## Validation

BenchhubPlus automatically validates all BenchHub configurations:

- **Problem Type**: Must be one of the 4 valid values
- **Target Type**: Must be either "General" or "Local"
- **Subject Type**: Must contain valid categories from the predefined list
- **Task Type**: Must be one of the 4 cognitive skill types
- **External Tool Usage**: Must be a boolean value

Invalid configurations will raise validation errors with specific guidance.

## Best Practices

### 1. Subject Type Selection
- Use coarse-grained categories for broad evaluations
- Use fine-grained subcategories for specific domain testing
- Combine multiple categories for comprehensive assessment

### 2. Problem Type Matching
- Use `MCQA` for objective knowledge testing
- Use `open-ended` for reasoning and value assessment
- Use `Binary` for simple classification tasks

### 3. Task Type Alignment
- `Knowledge` tasks work well with `MCQA` format
- `Reasoning` tasks benefit from `open-ended` format
- `Value` and `Alignment` tasks require subjective evaluation

### 4. Target Type Considerations
- Use `Local` for culture-specific evaluations
- Use `General` for universal knowledge assessment
- Consider language alignment with target type

## Migration from Legacy Formats

If you have existing configurations in older formats, use the migration utilities:

```python
from apps.core.schemas import PlanConfig

# Legacy format
legacy_config = {
    "language": "Korean",
    "subject_type": "Technology", 
    "task_type": "Programming"
}

# Convert to BenchHub format
benchhub_config = PlanConfig(
    problem_type="MCQA",  # Inferred from task
    target_type="General",  # Default
    subject_type=["Technology", "Tech./Computer Science"],  # Expanded
    task_type="Knowledge",  # Mapped from Programming
    external_tool_usage=False,  # Default
    language=legacy_config["language"],
    sample_size=100
)
```

## Troubleshooting

### Common Issues

1. **Invalid Subject Type**
   ```
   ValueError: Invalid subject_type 'Programming'. Must be one of the BenchHub categories.
   ```
   **Solution**: Use valid categories like `["Technology", "Tech./Computer Science"]`

2. **Empty Subject Type**
   ```
   ValueError: subject_type cannot be empty
   ```
   **Solution**: Provide at least one valid subject category

3. **Invalid Problem Type**
   ```
   ValueError: problem_type must be one of ['Binary', 'MCQA', 'short-form', 'open-ended']
   ```
   **Solution**: Use one of the four valid problem types

### Getting Help

For additional support with BenchHub configurations:

1. Check the validation error messages for specific guidance
2. Review the complete category list in `apps/core/schemas.py`
3. Use the example configurations as templates
4. Test configurations with the validation utilities

---

**Last Updated**: October 29, 2024  
**Version**: 2.0  
**Compatibility**: BenchhubPlus v2.0+