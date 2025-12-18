# 统一的实体字段配置
ENTITY_FIELDS = [
    {"type": "event_name", "name": "事件名称"},
    {"type": "content", "name": "内容"},
    {"type": "created_time", "name": "事件创建时间"},
    {"type": "action", "name": "行为"},
    {"type": "author", "name": "作者/出版方"},
    {"type": "brand", "name": "品牌"},
    {"type": "work", "name": "作品"},
    {"type": "dataset_model", "name": "数据集/模型"},
    {"type": "time_range", "name": "时间区间"},
    {"type": "end_time", "name": "结束时间"},
    {"type": "group", "name": "群体"},
    {"type": "holiday", "name": "节假日/纪念日"},
    {"type": "lifecycle_stage", "name": "生命周期阶段"},
    {"type": "location", "name": "地点"},
    {"type": "metric", "name": "指标"},
    {"type": "amount", "name": "金额"},
    {"type": "organization", "name": "机构"},
    {"type": "frequency", "name": "周期/频率"},
    {"type": "person", "name": "人员"},
    {"type": "platform", "name": "平台"},
    {"type": "product_service", "name": "产品/服务"},
    {"type": "rating", "name": "评价/评分"},
    {"type": "sentiment", "name": "情感倾向"},
    {"type": "start_time", "name": "开始时间"},
    {"type": "tag", "name": "标签"},
    {"type": "time", "name": "时间"},
    {"type": "topic", "name": "话题"}
]

# 生成JSON Schema的properties字段
_properties = {}
for field in ENTITY_FIELDS:
    _properties[field["type"]] = {"type": "string", "description": field["name"]}

# 生成JSON Schema(用于AI输出验证)
SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "description": "事件列表,允许为空数组",
            "items": {
                "type": "object",
                "properties": _properties,
                "required": []
            }
        }
    },
    "required": ["events"]
}
