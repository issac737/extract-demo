# 统一的实体字段配置
ENTITY_FIELDS = [
    "事件名称",
    "内容",
    "事件创建时间",
    "行为",
    "作者/出版方",
    "品牌",
    "作品",
    "数据集/模型",
    "时间区间",
    "结束时间",
    "群体",
    "节假日/纪念日",
    "生命周期阶段",
    "地点",
    "指标",
    "金额",
    "机构",
    "周期/频率",
    "人员",
    "平台",
    "产品/服务",
    "评价/评分",
    "情感倾向",
    "开始时间",
    "标签",
    "时间",
    "话题"
]

SCHEMA = {
    "type": "object",
    "properties": {
        "events": {
            "type": "array",
            "description": "事件列表，允许为空数组",
            "items": {
                "type": "object",
                "properties": {
                    "事件名称": {"type": "string", "description": "事件的标题或名称"},
                    "内容": {"type": "string", "description": "事件的详细描述"},
                    "事件创建时间": {"type": "string", "description": "事件发生或创建的时间"},
                    "行为": {"type": "string", "description": "事件中的主要行为或动作"},
                    "作者/出版方": {"type": "string", "description": "事件相关的作者或出版方"},
                    "品牌": {"type": "string", "description": "涉及的品牌"},
                    "作品": {"type": "string", "description": "相关作品"},
                    "数据集/模型": {"type": "string", "description": "涉及的数据集或模型"},
                    "时间区间": {"type": "string", "description": "事件持续的时间区间"},
                    "结束时间": {"type": "string", "description": "事件结束时间"},
                    "群体": {"type": "string", "description": "涉及的人群或群体"},
                    "节假日/纪念日": {"type": "string", "description": "相关节假日或纪念日"},
                    "生命周期阶段": {"type": "string", "description": "事件所处生命周期阶段"},
                    "地点": {"type": "string", "description": "事件发生地点"},
                    "指标": {"type": "string", "description": "相关指标或数据"},
                    "金额": {"type": "string", "description": "涉及的金额"},
                    "机构": {"type": "string", "description": "相关机构或组织"},
                    "周期/频率": {"type": "string", "description": "事件周期或频率"},
                    "人员": {"type": "string", "description": "涉及的人员"},
                    "平台": {"type": "string", "description": "相关平台"},
                    "产品/服务": {"type": "string", "description": "涉及的产品或服务"},
                    "评价/评分": {"type": "string", "description": "相关评价或评分"},
                    "情感倾向": {"type": "string", "description": "事件的情感倾向（正面/负面/中性）"},
                    "开始时间": {"type": "string", "description": "事件开始时间"},
                    "标签": {"type": "string", "description": "事件��签或分类"},
                    "时间": {"type": "string", "description": "事件相关时间"},
                    "话题": {"type": "string", "description": "事件相关话题"}
                },
                "required": []
            }
        }
    },
    "required": ["events"]
}
