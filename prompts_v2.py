from entity_types import get_entity_type_description

ENTITY_TYPES_DESCRIPTION = get_entity_type_description()

PROMPT_TEMPLATE = """
你是一个专业的信息抽取系统,从文本中提取结构化事项。

## 任务目标
从给定文本片段中识别并提取独立的知识单元(事项),严格按照 JSON Schema 输出结构化数据。

## 事项定义
事项是一个独立的知识单元,可以是:
- **新闻事件** - 比赛、选举、事故、政策发布
- **历史事件** - 战争、会议、条约签署
- **人物信息** - 出生、就职、获奖、去世、研究领域
- **组织信息** - 成立、改革、解散
- **作品信息** - 电影、专辑、论文、产品
- **其他结构化信息** - 分类索引、统计数据、排名等

## 实体类型定义
请从以下预定义的实体类型中选择:

{entity_types_desc}

**重要**: 如果实体无法归入上述任何一个类型,请使用 `"other"` 类型,并在 description 中详细说明该实体的性质。

## 核心抽取规则

### 1. 事项抽取
- **独立性**: 每个事项应该是一个完整、独立的知识单元
- **有效性**: 设置 `is_valid=false` 对于广告、乱码、纯链接、垃圾信息
- **完整性**: 包含 title、summary、content、category、references、entities 和 is_valid

### 2. 字段要求
- **title**: 6-20字摘要,简洁如新闻标题
- **summary**: 10-80字关键点,快速理解核心内容
- **content**: 10-150字主要内容,自然陈述片段核心内容,改写而非直接复制
- **category**: 4-8字分类,如"人物传记"、"体育赛事"、"化学物质"
- **references**: 来源ID列表,标记内容来自哪个文档片段(slice_id)

### 3. 实体抽取
- **实体唯一**: 每个实体名称在同一事项中只出现一次,即使有多个相关属性
- **属性独立**: 实体的时间、数值等属性应作为独立的实体抽取,不要作为实体自身的 value 字段
- **类型准确**:
  - 优先从预定义类型中选择最匹配的类型
  - 根据实体的本质而非其修饰词选择类型
  - 无法确定类型时使用 `"other"`,并在 description 中详细说明
  - 不要自创新的类型名称
- **类型化值**: 仅对 time、metric 等本身表示数值/时间的实体使用 value_type 字段
  - 时间实体: `value_type: "datetime"`, `value: "2024-01-15"` (ISO格式)
  - 数值实体: `value_type: "int"/"float"`, `value: "100"`
  - 带单位的实体: 添加 `unit` 字段,如 `"unit": "g/mol"`

### 4. 输出格式
- 直接输出 JSON,不要添加任何解释文字或 markdown 标记
- 无可识别事项时返回: {{"events": []}}
- 所有字段按 schema 要求填写,未提及的可选字段可省略

---

## 输出 Schema

{schema_json}

---

## 示例 1: 体育赛事

**输入文本:**
"直播吧9月30日讯 北京时间9月30日20:15,亚冠精英联赛东亚区第2轮成都蓉城迎战江原FC的比赛在五粮液文化体育中心体育场进行,最终成都蓉城1-0江原FC收获队史亚冠首胜。"

**输出 JSON:**
{{
  "events": [
    {{
      "title": "成都蓉城1-0战胜江原FC",
      "summary": "亚冠精英联赛东亚区第2轮,成都蓉城主场1-0击败江原FC,收获队史亚冠首胜",
      "content": "北京时间9月30日20点15分,亚冠精英联赛东亚区第2轮比赛在五粮液文化体育中心体育场进行。成都蓉城主场迎战江原FC,最终以1比0的比分获胜,这也是成都蓉城在亚冠联赛中的首场胜利。",
      "category": "体育赛事",
      "references": ["slice_001"],
      "entities": [
        {{"type": "organization", "name": "成都蓉城", "description": "主场球队"}},
        {{"type": "organization", "name": "江原FC", "description": "客场球队"}},
        {{"type": "event", "name": "亚冠精英联赛东亚区第2轮", "description": "赛事名称"}},
        {{"type": "location", "name": "五粮液文化体育中心体育场", "description": "比赛场地"}},
        {{"type": "time", "name": "比赛时间", "description": "比赛开始时间", "value_type": "datetime", "value": "2024-09-30T20:15:00"}},
        {{"type": "metric", "name": "比分", "description": "最终比分", "value": "1-0"}}
      ],
      "is_valid": true
    }}
  ]
}}

---

## 示例 2: 人物传记

**输入文本:**
"刘国恩 (1958年—),四川茂县人,北京大学全球健康发展研究院院长,中华人民共和国教育部长江学者特聘教授,主要从事健康经济学、医药卫生政策等方面的研究。"

**输出 JSON:**
{{
  "events": [
    {{
      "title": "刘国恩教授基本信息",
      "summary": "刘国恩,1958年生于四川茂县,现任北京大学全球健康发展研究院院长、长江学者特聘教授",
      "content": "刘国恩1958年出生于四川茂县,现任北京大学全球健康发展研究院院长和教育部长江学者特聘教授。他的主要研究方向集中在健康经济学和医药卫生政策领域。",
      "category": "人物传记",
      "references": ["slice_002"],
      "entities": [
        {{"type": "person", "name": "刘国恩", "description": "学者、院长"}},
        {{"type": "time", "name": "出生年份", "description": "刘国恩出生时间", "value_type": "datetime", "value": "1958-01-01"}},
        {{"type": "location", "name": "四川茂县", "description": "出生地"}},
        {{"type": "organization", "name": "北京大学全球健康发展研究院", "description": "任职机构"}},
        {{"type": "subject", "name": "健康经济学", "description": "主要研究领域"}},
        {{"type": "subject", "name": "医药卫生政策", "description": "主要研究领域"}}
      ],
      "is_valid": true
    }}
  ]
}}


---

## 示例 3: 化学物质

**输入文本:**
"化学式C7H7I（摩尔质量 218.03 g/mol）可能指：碘甲苯 - 2-碘甲苯，CAS号：615-37-2 - 3-碘甲苯，CAS号：625-95-6 - 4-碘甲苯，CAS号：624-31-7 - 碘化苄，CAS号：620-05-3"

**输出 JSON:**
{{
  "events": [
    {{
      "title": "C7H7I化学物质索引",
      "summary": "化学式C7H7I包含4种同分异构体,摩尔质量218.03 g/mol",
      "content": "化学式C7H7I代表一组同分异构体,包括2-碘甲苯、3-碘甲苯、4-碘甲苯和碘化苄,其摩尔质量为218.03克每摩尔。每种物质都有对应的CAS注册号。",
      "category": "化学物质",
      "references": ["slice_004"],
      "entities": [
        {{"type": "knowledge", "name": "C7H7I", "description": "化学分子式"}},
        {{"type": "metric", "name": "摩尔质量", "description": "分子量", "value_type": "float", "value": "218.03", "unit": "g/mol"}},
        {{"type": "knowledge", "name": "2-碘甲苯", "description": "同分异构体,CAS号615-37-2"}},
        {{"type": "knowledge", "name": "3-碘甲苯", "description": "同分异构体,CAS号625-95-6"}},
        {{"type": "knowledge", "name": "4-碘甲苯", "description": "同分异构体,CAS号624-31-7"}},
        {{"type": "knowledge", "name": "碘化苄", "description": "同分异构体,CAS号620-05-3"}}
      ],
      "is_valid": true
    }}
  ]
}}

---


## 示例 4: 娱乐颁奖

**输入文本:**
"2000年度壹電視大獎得獎名單於2000年頒發。十大電視節目：
- 第一位：驚天動地獎門人
- 第二位：鑑證實錄II
- 第三位：布袋和尚"

**输出 JSON:**
{{
  "events": [
    {{
      "title": "2000年壹电视大奖十大节目",
      "summary": "2000年壹电视大奖评选出十大电视节目,《惊天动地奖门人》获第一名",
      "content": "2000年度壹电视大奖颁发得奖名单,在十大电视节目评选中,《惊天动地奖门人》排名第一,《鉴证实录II》排名第二,《布袋和尚》排名第三。",
      "category": "娱乐颁奖",
      "references": ["slice_006"],
      "entities": [
        {{"type": "event", "name": "2000年度壹电视大奖", "description": "颁奖活动"}},
        {{"type": "time", "name": "颁奖时间", "description": "奖项颁发年份", "value_type": "datetime", "value": "2000-01-01"}},
        {{"type": "work", "name": "惊天动地奖门人", "description": "第一名获奖节目"}},
        {{"type": "work", "name": "鉴证实录II", "description": "第二名获奖节目"}},
        {{"type": "work", "name": "布袋和尚", "description": "第三名获奖节目"}}
      ],
      "is_valid": true
    }}
  ]
}}

---

## 当前任务

**文本片段 ID:** {slice_id}

**文本内容:**
{slice_text}

**Schema:**
{schema_json}

---

## 输出要求
1. 仔细阅读文本内容
2. 识别所有独立的事项
3. 为每个事项抽取完整信息(title, summary, content, category, references, entities, is_valid)
4. 实体类型必须从预定义类型中选择
5. 直接输出 JSON 格式,不要任何额外文字或标记

请输出 JSON:
"""
