"""
实体类型定义配置 - 基于 WHO/WHAT/WHEN/WHERE/ABOUT 维度划分
"""

ENTITY_TYPES = {
    # ===== WHO - 主体 =====
    "who": {
        "person": {
            "name": "人物",
            "definition": "真实或虚构的个人",
            "examples": ["马斯克", "刘国恩", "孙悟空"]
        },
        "organization": {
            "name": "机构",
            "definition": "机构、公司、学校、实验室",
            "examples": ["特斯拉", "北京大学", "国务院"]
        },
        "group": {
            "name": "群体",
            "definition": "群体、人群、族群、团队",
            "examples": ["粉丝群", "青少年", "汉族"]
        }
    },

    # ===== WHAT - 客体 =====
    "what": {
        "organism": {
            "name": "动植物",
            "definition": "动植物、微生物",
            "examples": ["大熊猫", "银杏树", "新冠病毒"]
        },
        "offering": {
            "name": "产品服务",
            "definition": "产品或者服务，例如：一双鞋;一张演唱会门票;租车;理发;或者在线直播的电视节目",
            "examples": ["Model 3", "演唱会门票", "理发服务"]
        },
        "work": {
            "name": "作品",
            "definition": "作品（论文、影视、文章、专辑）",
            "examples": ["《流浪地球》", "Nature论文", "《夜曲》"]
        },
        "project": {
            "name": "项目",
            "definition": "项目、计划、工程",
            "examples": ["阿波罗计划", "西部大开发", "5G建设工程"]
        },
        "brand": {
            "name": "品牌",
            "definition": "品牌",
            "examples": ["苹果", "可口可乐", "Nike"]
        },
        "platform": {
            "name": "平台",
            "definition": "平台、网站、系统",
            "examples": ["淘宝", "Twitter", "微信"]
        },
        "knowledge": {
            "name": "知识",
            "definition": "生物化学名词、医疗名词、算法模型、法律概念、公式等",
            "examples": ["深度学习", "C7H7I", "糖尿病", "民法典"]
        },
        "policy": {
            "name": "政策",
            "definition": "政策、制度",
            "examples": ["双减政策", "碳中和目标", "最低工资制度"]
        },
        "event": {
            "name": "事件",
            "definition": "事件、活动、赛事",
            "examples": ["世界杯", "亚冠精英联赛", "地震", "颁奖典礼"]
        },
        "award": {
            "name": "奖项",
            "definition": "奖项、荣誉、勋章、称号",
            "examples": ["诺贝尔奖", "奥斯卡奖", "荣誉军团勋章", "院士称号"]
        }
    },

    # ===== WHEN - 时间 =====
    "when": {
        "time": {
            "name": "时间点",
            "definition": "时间点",
            "examples": ["2024-09-30T20:15:00", "2016年4月28日"]
        },
        "time_range": {
            "name": "时间区间",
            "definition": "时间区间",
            "examples": ["2020-2023年", "唐朝", "冷战时期"]
        },
        "holiday": {
            "name": "节假日",
            "definition": "节假日、纪念日",
            "examples": ["春节", "国庆节", "世界环境日"]
        },
        "state": {
            "name": "��态",
            "definition": "状态，比如事件状态（进行中/已完成/取消、产品上市/下架，获奖提名/落选等等）",
            "examples": ["进行中", "已完成", "取消", "上市", "获奖"]
        },
        "period": {
            "name": "时期",
            "definition": "时期、时代、年代",
            "examples": ["文艺复兴时期", "90年代", "战国时期"]
        }
    },

    # ===== WHERE - 空间 =====
    "where": {
        "location": {
            "name": "地点",
            "definition": "地点、地理坐标等",
            "examples": ["上海", "五粮液文化体育中心", "喜马拉雅山"]
        }
    },

    # ===== ABOUT - 主题/度量/现象/行为 =====
    "about": {
        "subject": {
            "name": "话题",
            "definition": "话题、学科、领域、研究方向、主题",
            "examples": ["人工智能", "健康经济学", "体育", "教育改革"]
        },
        "metric": {
            "name": "度量",
            "definition": "比分、排名、得分、价格",
            "examples": ["1-0", "第一名", "218.03 g/mol", "8人"]
        },
        "phenomenon": {
            "name": "现象",
            "definition": "现象，比如全球变暖、通货膨胀",
            "examples": ["全球变暖", "通货膨胀", "人口老龄化"]
        },
        "action": {
            "name": "行为",
            "definition": "行为",
            "examples": ["签约", "发布", "收购", "投票"]
        }
    }
}


def get_all_entity_types():
    """获取所有实体类型的列表"""
    all_types = []
    for dimension, types in ENTITY_TYPES.items():
        all_types.extend(types.keys())
    return all_types


def get_entity_type_description():
    """生成实体类型的详细描述文本,用于Prompt"""
    lines = []

    dimension_names = {
        "who": "WHO - 主体",
        "what": "WHAT - 客体",
        "when": "WHEN - 时间",
        "where": "WHERE - 空间",
        "about": "ABOUT - 主题/度量/现象/行为"
    }

    for dimension, types in ENTITY_TYPES.items():
        lines.append(f"\n### {dimension_names[dimension]}")
        for type_key, type_info in types.items():
            examples_str = "、".join(type_info["examples"])
            lines.append(
                f"- **{type_key}** ({type_info['name']}): "
                f"{type_info['definition']} "
                f"| 示例: {examples_str}"
            )

    return "\n".join(lines)


def get_entity_type_mapping():
    """获取实体类型标识符到中文名称的映射"""
    mapping = {}
    for dimension, types in ENTITY_TYPES.items():
        for type_key, type_info in types.items():
            mapping[type_key] = type_info["name"]
    return mapping


if __name__ == "__main__":
    # 测试输出
    print("所有实体类型:", get_all_entity_types())
    print("\n" + "="*80)
    print("实体类型描述:")
    print(get_entity_type_description())
    print("\n" + "="*80)
    print("类型映射:", get_entity_type_mapping())
