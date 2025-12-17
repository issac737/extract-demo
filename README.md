# 新闻事件抽取系统

一个基于 AI 的新闻事件自动抽取工具,从新闻网页中提取结构化事件信息。

## 功能特点

- ✅ 支持从新闻URL自动提取文章内容
- ✅ 使用滑动窗口策略进行智能切片
- ✅ AI 驱动的事件抽取,支持27个标准化字段
- ✅ 基于内容相似度的智能去重
- ✅ 支持批量处理多个URL
- ✅ 统一的事件字段配置

## 安装依赖

```bash
pip install huggingface_hub requests lxml
```

## 配置

### 1. 设置 API Token

```bash
# Linux/Mac
export HF_TOKEN=your_huggingface_token

# Windows PowerShell
$env:HF_TOKEN="your_huggingface_token"
```

### 2. 准备URL列表

在 `links.txt` 中添加要处理的新闻URL,每行一个:

```
https://news.sina.com.cn/c/2025-12-17/doc-xxxxx.shtml
https://news.sina.com.cn/c/2025-12-17/doc-yyyyy.shtml
```

## 使用方法

```bash
python main.py
```

## 输出字段

系统支持以下27个标准化字段:

- **基本信息**: 事件名称、内容、事件创建时间
- **主体信息**: 人员、机构、群体
- **时间信息**: 时间、开始时间、结束时间、时间区间
- **地点信息**: 地点
- **行为信息**: 行为
- **分类信息**: 标签、话题、情感倾向
- **其他**: 品牌、产品/服务、平台���作者/出版方、指标、金额等

## 配置参数

### 切片策略 (main.py)

```python
window_size = 3   # 窗口大小(段落数)
overlap = 1       # 重叠大小(段落数)
min_length = 10   # 最小段落长度
```

### 去重策略 (main.py)

```python
content_threshold = 0.75  # 内容相似度阈值(0-1)
```

## 项目结构

```
.
├── main.py              # 主程序
├── config.py           # Schema配置
├── prompts.py          # 提示词模板
├── links.txt           # URL列表
├── extracted_events.json  # 输出结果
└── README.md           # 项目说明
```

## 注意事项

- 确保 HuggingFace API 有足够的免费额度
- 新闻网站需要可访问(无需登录)
- 建议使用中文新闻网站以获得更好效果

## 许可证

MIT License
