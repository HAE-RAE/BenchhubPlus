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

Hierarchical subject categorization system with 6 coarse-grained categories and 250 fine-grained subcategories.

#### Coarse-Grained Categories (6)

1. **Art & Sports**
2. **Culture**
3. **HASS**
4. **Science**
5. **Social Intelligence**
6. **Tech.**

#### Fine-Grained Subcategories (250)

**Art & Sports (68 subcategories):**
- `Art & Sports/Architecture`
- `Art & Sports/Clothing`
- `Art & Sports/Education`
- `Art & Sports/Fashion`
- `Art & Sports/Festivals`
- `Art & Sports/Food`
- `Art & Sports/Language`
- `Art & Sports/Literature`
- `Art & Sports/Media`
- `Art & Sports/Music`
- `Art & Sports/Painting`
- `Art & Sports/Performing`
- `Art & Sports/Photography`
- `Art & Sports/Sculpture`
- `Art & Sports/Sports`
- `Art & Sports/Urban Eng.`
- `Art & Sports/arts&sports/animal`
- `Art & Sports/arts&sports/animal_life`
- `Art & Sports/arts&sports/animals`
- `Art & Sports/arts&sports/animation`
- `Art & Sports/arts&sports/anime`
- `Art & Sports/arts&sports/art`
- `Art & Sports/arts&sports/arts`
- `Art & Sports/arts&sports/artwork`
- `Art & Sports/arts&sports/barking`
- `Art & Sports/arts&sports/boat`
- `Art & Sports/arts&sports/branding`
- `Art & Sports/arts&sports/character`
- `Art & Sports/arts&sports/collecting`
- `Art & Sports/arts&sports/dance`
- `Art & Sports/arts&sports/design`
- `Art & Sports/arts&sports/digital_design`
- `Art & Sports/arts&sports/dog`
- `Art & Sports/arts&sports/dogs`
- `Art & Sports/arts&sports/drink`
- `Art & Sports/arts&sports/equestrian`
- `Art & Sports/arts&sports/fantasy`
- `Art & Sports/arts&sports/farming`
- `Art & Sports/arts&sports/fiction`
- `Art & Sports/arts&sports/fitness`
- `Art & Sports/arts&sports/flower`
- `Art & Sports/arts&sports/furniture`
- `Art & Sports/arts&sports/game`
- `Art & Sports/arts&sports/gaming`
- `Art & Sports/arts&sports/graphics`
- `Art & Sports/arts&sports/illustration`
- `Art & Sports/arts&sports/infographic`
- `Art & Sports/arts&sports/landscape`
- `Art & Sports/arts&sports/landscapes`
- `Art & Sports/arts&sports/nature`
- `Art & Sports/arts&sports/poetry`
- `Art & Sports/arts&sports/puzzle`
- `Art & Sports/arts&sports/reading`
- `Art & Sports/arts&sports/scenic`
- `Art & Sports/arts&sports/speech`
- `Art & Sports/arts&sports/toy`
- `Art & Sports/arts&sports/transportation`
- `Art & Sports/arts&sports/typography`
- `Art & Sports/arts&sports/urban`
- `Art & Sports/arts&sports/urban_art`
- `Art & Sports/arts&sports/urban_design`
- `Art & Sports/arts&sports/urban_environment`
- `Art & Sports/arts&sports/urban_life`
- `Art & Sports/arts&sports/urbanism`
- `Art & Sports/arts&sports/video_games`
- `Art & Sports/arts&sports/website`
- `Art & Sports/arts&sports/wine`
- `Art & Sports/arts&sports/zoology`

**Culture (14 subcategories):**
- `Culture/Celebration Holiday`
- `Culture/Clothing`
- `Culture/Daily Life`
- `Culture/Family`
- `Culture/Food`
- `Culture/Holiday`
- `Culture/Housing`
- `Culture/Leisure`
- `Culture/Tradition`
- `Culture/Work Life`
- `Culture/culture/attractions`
- `Culture/culture/friendship`
- `Culture/culture/hobbies`
- `Culture/culture/nature`

**HASS (68 subcategories):**
- `HASS/Administration`
- `HASS/Art & Sports`
- `HASS/Biology`
- `HASS/Celebration Holiday`
- `HASS/Cognitive Studies`
- `HASS/Culture`
- `HASS/Daily Life`
- `HASS/Economics`
- `HASS/Education`
- `HASS/Family`
- `HASS/Food`
- `HASS/Geography`
- `HASS/HASS`
- `HASS/History`
- `HASS/Language`
- `HASS/Law`
- `HASS/Literature`
- `HASS/Math`
- `HASS/Media`
- `HASS/Music`
- `HASS/Philosophy`
- `HASS/Physics`
- `HASS/Politics`
- `HASS/Psychology`
- `HASS/Religion`
- `HASS/Sports`
- `HASS/Tech.`
- `HASS/Trade`
- `HASS/Tradition`
- `HASS/Urban Eng.`
- `HASS/Welfare`
- `HASS/Work Life`
- `HASS/social&humanity/animal_welfare`
- `HASS/social&humanity/biography`
- `HASS/social&humanity/branding`
- `HASS/social&humanity/celebrity`
- `HASS/social&humanity/communication`
- `HASS/social&humanity/crime`
- `HASS/social&humanity/customer_support`
- `HASS/social&humanity/data_science`
- `HASS/social&humanity/database`
- `HASS/social&humanity/databases`
- `HASS/social&humanity/date`
- `HASS/social&humanity/dates`
- `HASS/social&humanity/datetime`
- `HASS/social&humanity/director`
- `HASS/social&humanity/drama`
- `HASS/social&humanity/environment`
- `HASS/social&humanity/fiction`
- `HASS/social&humanity/finance`
- `HASS/social&humanity/friendship`
- `HASS/social&humanity/health`
- `HASS/social&humanity/hero`
- `HASS/social&humanity/identity`
- `HASS/social&humanity/leadership`
- `HASS/social&humanity/library`
- `HASS/social&humanity/lifestyle`
- `HASS/social&humanity/management`
- `HASS/social&humanity/museum`
- `HASS/social&humanity/organizations`
- `HASS/social&humanity/privacy`
- `HASS/social&humanity/real_estate`
- `HASS/social&humanity/sociology`
- `HASS/social&humanity/technology`
- `HASS/social&humanity/transport`
- `HASS/social&humanity/transportation`
- `HASS/social&humanity/website`
- `HASS/social&humanity/workplace`

**Science (20 subcategories):**
- `Science/Astronomy`
- `Science/Atmospheric Science`
- `Science/Biology`
- `Science/Biomedical Eng.`
- `Science/Chemistry`
- `Science/Earth Science`
- `Science/Electrical Eng.`
- `Science/Geology`
- `Science/History`
- `Science/Language`
- `Science/Life Science`
- `Science/Math`
- `Science/Physics`
- `Science/Religion`
- `Science/Statistics`
- `Science/science/color`
- `Science/science/dna`
- `Science/science/dna2protein`
- `Science/science/numerology`
- `Science/science/plant`

**Social Intelligence (18 subcategories):**
- `Social Intelligence/Bias`
- `Social Intelligence/Commonsense`
- `Social Intelligence/Language`
- `Social Intelligence/Norms`
- `Social Intelligence/Value/Alignment`
- `Social Intelligence/misc/abstract`
- `Social Intelligence/misc/animal`
- `Social Intelligence/misc/cliche`
- `Social Intelligence/misc/color`
- `Social Intelligence/misc/diagnosis`
- `Social Intelligence/misc/durable`
- `Social Intelligence/misc/hate_crime`
- `Social Intelligence/misc/health`
- `Social Intelligence/misc/idiomatic_expression`
- `Social Intelligence/misc/norm`
- `Social Intelligence/misc/proverb`
- `Social Intelligence/misc/thinking`
- `Social Intelligence/misc/wellbeing`

**Tech. (62 subcategories):**
- `Tech./AI`
- `Tech./Aerospace Eng.`
- `Tech./Agricultural Eng.`
- `Tech./Biomedical Eng.`
- `Tech./Chemical Eng.`
- `Tech./Civil Eng.`
- `Tech./Coding`
- `Tech./Electrical Eng.`
- `Tech./Energy`
- `Tech./Environmental Eng.`
- `Tech./Food`
- `Tech./Geography`
- `Tech./IT`
- `Tech./Marine Eng.`
- `Tech./Materials Eng.`
- `Tech./Mechanics`
- `Tech./Nuclear Eng.`
- `Tech./Physics`
- `Tech./Urban Eng.`
- `Tech./tech/aircraft`
- `Tech./tech/airline`
- `Tech./tech/airlines`
- `Tech./tech/algorithm`
- `Tech./tech/animal`
- `Tech./tech/animal_welfare`
- `Tech./tech/animation`
- `Tech./tech/aquarium`
- `Tech./tech/automotive`
- `Tech./tech/aviation`
- `Tech./tech/azure`
- `Tech./tech/boat`
- `Tech./tech/cloud`
- `Tech./tech/communication`
- `Tech./tech/communications`
- `Tech./tech/cv`
- `Tech./tech/database`
- `Tech./tech/db`
- `Tech./tech/dice`
- `Tech./tech/ethereum`
- `Tech./tech/finance`
- `Tech./tech/financial`
- `Tech./tech/geo_loc`
- `Tech./tech/geolocation`
- `Tech./tech/graphics`
- `Tech./tech/ios`
- `Tech./tech/marine_biology`
- `Tech./tech/marine_eng`
- `Tech./tech/mobile`
- `Tech./tech/monitoring`
- `Tech./tech/network`
- `Tech./tech/ocr`
- `Tech./tech/office`
- `Tech./tech/programming`
- `Tech./tech/real_estate`
- `Tech./tech/remote_sensing`
- `Tech./tech/robotics`
- `Tech./tech/secure`
- `Tech./tech/security`
- `Tech./tech/transportation`
- `Tech./tech/uuid`
- `Tech./tech/vehicle`
- `Tech./tech/voice`

**Example:**
```json
{
  "subject_type": ["Tech.", "Tech./Coding"]
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
  "subject_type": ["Tech.", "Tech./Electrical Eng."],
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
    subject_type=["Science", "Science/Math"],
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
  "subject_type": ["Tech.", "Tech./Coding"],
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
      subject_type: ["Tech.", "Tech./Coding"]
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
  "subject_type": ["Science", "Science/Math", "Science/Physics"]
}
```

### Complex Filter Combination
```json
{
  "problem_type": "open-ended",
  "target_type": "Local",
  "subject_type": ["Culture", "Culture/Tradition"],
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
    "subject_type": "Tech.",
    "task_type": "Programming"
}

# Convert to BenchHub format
benchhub_config = PlanConfig(
    problem_type="MCQA",  # Inferred from task
    target_type="General",  # Default
    subject_type=["Tech.", "Tech./Coding"],  # Expanded
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
   **Solution**: Use valid categories like `["Tech.", "Tech./Coding"]`

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