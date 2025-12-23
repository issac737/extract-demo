import os
import json
import requests
from lxml import etree
from difflib import SequenceMatcher
from config import SCHEMA
from prompts_v2 import PROMPT_TEMPLATE
from siliconflow_client import SiliconFlowClient

# 读取 .env 文件
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()

# 初始化 SiliconFlow API 客户端
client = SiliconFlowClient()

def read_document(file_path):
    # 读取本地文件内容，转换为MD格式
    if file_path.startswith('http'):
        response = requests.get(file_path)
        response.raise_for_status()
        tree = etree.HTML(response.content)
        title_elements = tree.xpath('/html/head/title/text()')
        title = title_elements[0] if title_elements else "网页内容"

        # 提取链接里的文本
        paragraphs = []
        selectors = [
            '//div[@id="artibody"]//p//text()',  
            '//div[@id="article"]//p//text()',
            '//article//p//text()',
            '//div[contains(@class,"article")]//p//text()',
            '//div[contains(@class,"content")]//p//text()',
            '//p//text()',  
        ]

        for selector in selectors:
            paragraphs = tree.xpath(selector)
            # 过滤空白和过短的文本
            paragraphs = [p.strip() for p in paragraphs if p.strip() and len(p.strip()) > 10]
            if len(paragraphs) > 3:  
                break

        if not paragraphs:
            raise ValueError(f"无法从网页中提取内容: {file_path}")

        content = f"# {title}\n\n" + '\n\n'.join(paragraphs)
    elif file_path.endswith('.txt') or file_path.endswith('.md'):
        # TXT或MD文件
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        content = '\n\n'.join(paragraphs)  
    else:
        raise ValueError("不支持的文件格式或URL")
    return content

def segment_into_slices(content, window_size=3, overlap=1, min_length=10):
    """
    滑动窗口
    参数:    
        window_size: 窗口大小(段落数)
        overlap: 重叠大小(段落数)
        min_length: 过滤过短段落，比如责编名字

    """
    # 按段落分割
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

    # 过滤过短的段落
    paragraphs = [p for p in paragraphs if len(p) >= min_length]

    if not paragraphs:
        return []

    slices = []
    step = window_size - overlap  # 滑动步长

    for i in range(0, len(paragraphs), step):
        slice_paragraphs = paragraphs[i:i+window_size]
        if len(slice_paragraphs) > 0:
            slice_text = '\n\n'.join(slice_paragraphs)
            slices.append(slice_text.strip())

        # 如果已经到达或超过最后一个段落,停止
        if i + window_size >= len(paragraphs):
            break

    return slices

def extract_events_from_slice(slice_text, slice_id):
    from entity_types import get_entity_type_description

    schema_json = json.dumps(SCHEMA, ensure_ascii=False, indent=2)
    entity_types_desc = get_entity_type_description()

    prompt = PROMPT_TEMPLATE.format(
        slice_id=slice_id,
        slice_text=slice_text,
        schema_json=schema_json,
        entity_types_desc=entity_types_desc
    )

    try:
        response = client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000
        )
        result = response.choices[0].message.content.strip()
    except Exception as e:
        print(f"模型调用失败:{e}")
        return []

    if '```json' in result:
        start = result.find('```json') + 7
        end = result.find('```', start)
        result = result[start:end].strip()
    else:
        l = result.find('{')
        r = result.rfind('}')
        if l != -1 and r != -1 and r > l:
            result = result[l:r+1]
        else:
            return []

    try:
        data = json.loads(result)
    except Exception:
        return []

    if isinstance(data, dict):
        events = data.get("events", [])
        return events if isinstance(events, list) else []

    if isinstance(data, list):
        return data

    return []

def deduplicate_events(events, content_threshold=0.75, key_field_threshold=0.8):
    """
    基于内容相似度和关键字段匹配的智能去重与合并

    策略:
    1. 【优先】如果关键字段(time、location、person、organization)高度相似 → 同一事件的不同角度描述,智能合并
    2. 如果内容高度相似 > content_threshold → 完全重复的事件,保留更长版本
    """
    if not events:
        return []

    unique_events = []

    for event in events:
        event_content = event.get("content", "")
        event_title = event.get("title", "")  # 改为使用 title 字段

        # 跳过无效事件或内容为空的事件
        if not event_content or not event_title:
            continue

        is_duplicate = False
        merge_index = -1

        for i, unique_event in enumerate(unique_events):
            unique_content = unique_event.get("content", "")
            unique_title = unique_event.get("title", "")

            # 先检查标题相似度
            title_sim = SequenceMatcher(None, event_title, unique_title).ratio()
            if title_sim >= 0.85:  # 标题高度相似,可能是同一事项
                merge_index = i
                break

            # 内容高度相似判断
            content_sim = SequenceMatcher(None, event_content, unique_content).ratio()
            if content_sim >= content_threshold:
                is_duplicate = True
                if len(event_content) > len(unique_content):
                    unique_events[i] = event
                break

        if merge_index >= 0:
            # 合并事件:保留更详细的字段,合并描述
            merged_event = _merge_events(unique_events[merge_index], event)
            unique_events[merge_index] = merged_event
        elif not is_duplicate:
            unique_events.append(event)

    return unique_events

def _merge_events(event1, event2):
    """
    合并两个事件,保留更详细的字段值,并智能合并描述
    """
    merged = {}

    # 获取所有字段
    all_fields = set(event1.keys()) | set(event2.keys())

    for field in all_fields:
        value1 = event1.get(field, "")
        value2 = event2.get(field, "")

        # 特殊处理"content"字段:智能合并描述
        if field == "content":
            if value1 and value2:
                # 计算描述相似度
                sim = SequenceMatcher(None, value1, value2).ratio()
                if sim >= 0.75:
                    # 相似度高,保留更长的描述
                    merged[field] = value1 if len(value1) > len(value2) else value2
                else:
                    # 相似度低,用句号拼接
                    merged[field] = f"{value1}。{value2}"
            else:
                merged[field] = value1 or value2

        # 特殊处理"event_name"字段:选择更完整的名称
        elif field == "event_name":
            if value1 and value2:
                # 选择更长/更详细的名称
                merged[field] = value1 if len(value1) > len(value2) else value2
            else:
                merged[field] = value1 or value2

        # 特殊处理列表型字段(person、organization等):合并去重
        elif field in ["person", "organization", "tag", "topic"]:
            if value1 and value2:
                # 用逗号分割,合并后去重
                items1 = set(v.strip() for v in str(value1).split(',') if v.strip())
                items2 = set(v.strip() for v in str(value2).split(',') if v.strip())
                merged_items = items1 | items2
                merged[field] = ','.join(sorted(merged_items))
            else:
                merged[field] = value1 or value2

        # 其他字段:保留更长/更详细的值
        else:
            if len(str(value1)) >= len(str(value2)):
                merged[field] = value1
            else:
                merged[field] = value2

    return merged

def main():
    # 读取test_data文件夹中的测试数据
    test_data_folder = r"C:\Users\PC\Desktop\git demo\test_data"
    metadata_path = os.path.join(test_data_folder, "metadata.json")

    print(f"\n{'='*80}")
    print(f"AI事件抽取系统")
    print(f"{'='*80}")

    # 检查是否存在测试数据
    if not os.path.exists(metadata_path):
        print(f"未找到测试数据!")
        print(f"{'='*80}")
        return

    # 读取元数据
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    print(f"\n测试数据信息:")
    print(f"  抽取时间: {metadata.get('extraction_date', 'Unknown')}")
    print(f"  总文件数: {metadata.get('total_files', 0)}")
    print(f"  随机种子: {metadata.get('random_seed', 'Unknown')}")
    print("="*80)

    # 获取所有测试文件
    input_files = []
    for relative_path in metadata.get('file_list', []):
        file_path = os.path.join(test_data_folder, relative_path)
        if os.path.exists(file_path):
            input_files.append(file_path)
        else:
            print(f"警告: 文件不存在 {file_path}")

    if not input_files:
        print(f"未找到有效的测试文件!")
        print(f"{'='*80}")
        return

    print(f"\n从文件夹读取: {test_data_folder}")
    print(f"共加载 {len(input_files)} 个测试文件")
    print("="*80)

    all_events = []
    output_file = 'extracted_events.json'
    temp_output_file = 'extracted_events_temp.json'

    # 每处理N个文件保存一次
    save_interval = 10

    for file_index, file_path in enumerate(input_files, 1):
        file_name = os.path.basename(file_path)
        relative_path = os.path.relpath(file_path, test_data_folder)
        print(f"\n[{file_index}/{len(input_files)}] 处理文件: {relative_path}")
        print("-" * 80)

        try:
            # 读取文件内容
            content = read_document(file_path)

            # 检查内容是否为空或太短
            if not content or len(content.strip()) < 50:
                print(f"文件内容为空或过短 (长度: {len(content.strip())})")
                continue

            print(f"内容长度: {len(content)} 字符")

            # 分割段落&切片
            slices = segment_into_slices(content)

            if not slices:
                print(f"无法生成有效切片")
                continue

            print(f"切片数量: {len(slices)}")

            # 提取事件
            file_events_count = 0
            file_events = []  # 当前文件的事件列表
            for i, slice_text in enumerate(slices):
                slice_id = f"{file_name}_slice_{i+1}"
                print(f"  处理切片 {i+1}/{len(slices)}...", end="", flush=True)

                try:
                    events = extract_events_from_slice(slice_text, slice_id)
                    file_events.extend(events)
                    file_events_count += len(events)
                    if len(events) > 0:
                        print(f" {len(events)} 个事件")
                    else:
                        print(f" 无事件")
                except Exception as slice_error:
                    print(f" 失败: {slice_error}")
                    continue

            # 文件处理完成后,立即对当前文件的事件进行去重
            if file_events:
                before_dedup = len(file_events)
                file_events = deduplicate_events(file_events, content_threshold=0.75)
                after_dedup = len(file_events)
                removed = before_dedup - after_dedup

                print(f"文件完成,提取 {file_events_count} 个事件,去重后保留 {after_dedup} 个" +
                      (f" (去除 {removed} 个重复)" if removed > 0 else ""))

                # 添加到总事件列表
                all_events.extend(file_events)
            else:
                print(f"文件完成,未提取到事件")

        except Exception as e:
            print(f"处理文件时出错: {e}")
            continue

        # 增量保存: 每处理N个文件保存一次中间结果
        if file_index % save_interval == 0 or file_index == len(input_files):
            print(f"\n保存中间结果 ({file_index}/{len(input_files)} 文件已处理)...")
            with open(temp_output_file, 'w', encoding='utf-8') as f:
                json.dump(all_events, f, ensure_ascii=False, indent=2)
            print(f"   已保存 {len(all_events)} 个事件到 {temp_output_file}")

    print(f"\n{'='*80}")
    print(f"统计信息:")
    original_count = len(all_events)
    print(f"去重前事件数: {original_count}")

    # 去重
    all_events = deduplicate_events(all_events, content_threshold=0.75)
    print(f"去重后事件数: {len(all_events)}")
    print(f"去除重复: {original_count - len(all_events)} 个")
    print(f"{'='*80}")
 
    # 输出最终结果并保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)

    print(f"\n    最终结果已保存到: {output_file}")
    print(f"共提取有效事件: {len(all_events)} 个")

    # 打印前几个事件作为预览
    if all_events and len(all_events) > 0:
        print(f"\n预览前 {min(3, len(all_events))} 个事件:")
        print(json.dumps(all_events[:3], ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()