# Schema 定义 - 用于 prompts_v2.py
# 注意: prompts_v2.py 中包含完整的实体定义和示例,这里只是用于验证的基础schema

SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "description": "从当前内容提取的事项列表 - 每个事项是一个独立的知识单元。如果没有有效数据，返回空数组",
            "items": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "6-20字摘要 - 简洁如新闻标题"
                    },
                    "summary": {
                        "type": "string",
                        "description": "10-80字关键点 - 快速理解核心内容"
                    },
                    "content": {
                        "type": "string",
                        "description": "10-150字主要内容 - 自然陈述片段核心内容，改写关键信息而非复制"
                    },
                    "category": {
                        "type": "string",
                        "description": "4-8字分类 - 如'人物传记'、'影片信息'、'职业生涯'"
                    },
                    "references": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "database中的section_id或message_id"
                        },
                        "minItems": 1,
                        "description": "来源ID列表 - 准确列出内容实际来自哪些ID"
                    },
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {
                                    "type": "string",
                                    "description": "实体类型 - 从database定义中选择。搜索优化：乐队→organization，作品→work，人物→person"
                                },
                                "name": {
                                    "type": "string",
                                    "description": "实体名称 - 使用原文表达，不要多次提取相同的实体名称"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "实体描述 - 角色、功能、具体来源等补充信息"
                                },
                                "value_type": {
                                    "type": "string",
                                    "enum": ["text", "int", "float", "datetime", "bool"],
                                    "description": "值类型 - 根据实体类型进行类型化提取，如价格、数量、时间、布尔值"
                                },
                                "value": {
                                    "type": "string",
                                    "description": "标准化值 - 数字原样，日期时间ISO格式(2024-01-15)，布尔值true/false"
                                },
                                "unit": {
                                    "type": "string",
                                    "description": "单位（如适用）- 元/天/个/公斤等"
                                }
                            },
                            "required": ["type", "name", "description"]
                        },
                        "description": "从内容中提取的实体 - 提取完整的实体名称和相关属性"
                    },
                    "is_valid": {
                        "type": "boolean",
                        "description": "事项有效性：true=有效内容，false=无效（广告/乱码/纯链接/垃圾信息）"
                    }
                },
                "required": ["title", "summary", "content", "category", "references", "entities", "is_valid"]
            },
            "minItems": 1
        }
    },
    "required": ["events"]
}

