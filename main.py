import os
import json
from huggingface_hub import InferenceClient
import requests
from lxml import etree
from difflib import SequenceMatcher
from config import SCHEMA
from prompts import PROMPT_TEMPLATE

# 初始化 HuggingFace Inference API 
hf_token = os.getenv('HF_TOKEN')
if not hf_token:
    raise ValueError("未设置 HF_TOKEN 环境变量")
client = InferenceClient(model="Qwen/Qwen2.5-7B-Instruct")

def read_document(file_path):
    # 读取网页或本地文件内容，转换为MD格式
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
    elif file_path.endswith('.txt'):
        # TXT文件
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
    schema_json = json.dumps(SCHEMA, ensure_ascii=False, indent=2)
    prompt = PROMPT_TEMPLATE.format(
        slice_id=slice_id,
        slice_text=slice_text,
        schema_json=schema_json
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

def deduplicate_events(events, content_threshold=0.75):
    """
    基于内容相似度去重

    1. 比较事件内容的相似度
    2. 相似度 > 阈值 → 认为是重复
    3. 保留内容更详细的版本
    """
    if not events:
        return []

    unique_events = []

    for event in events:
        event_content = event.get("内容", "")
        event_name = event.get("事件名称", "")

        if not event_content or not event_name:
            continue

        is_duplicate = False

        for i, unique_event in enumerate(unique_events):
            unique_content = unique_event.get("内容", "")
            sim = SequenceMatcher(None, event_content, unique_content).ratio()
            if sim >= content_threshold:
                # 发现重复,保留内容更长的版本
                is_duplicate = True
                if len(event_content) > len(unique_content):
                    unique_events[i] = event
                break

        if not is_duplicate:
            unique_events.append(event)

    return unique_events

def main():
    # 从links.txt读取URL列表
    if not os.path.exists('links.txt'):
        print("links.txt文件不存在。")
        return
    
    with open('links.txt', 'r', encoding='utf-8') as f:
        input_urls = [line.strip() for line in f if line.strip()]
    
    all_events = []

    print(f"\n共找到 {len(input_urls)} 个URL")
    print("=" * 80)

    for url_index, url in enumerate(input_urls, 1):
        print(f"\n[{url_index}/{len(input_urls)}] 处理网页: {url}")
        print("-" * 80)

        try:
            # 读取网页内容并改为md格式
            content = read_document(url)
            print(f"  ✓ 内容长度: {len(content)} 字符")

            # 分割段落&切片
            slices = segment_into_slices(content)
            print(f"  ✓ 切片数量: {len(slices)}")

            # 提取事件
            url_events_count = 0
            for i, slice_text in enumerate(slices):
                slice_id = f"{url}_slice_{i+1}"
                print(f"  处理切片 {i+1}/{len(slices)}...", end="")
                events = extract_events_from_slice(slice_text, slice_id)
                all_events.extend(events)
                url_events_count += len(events)
                print(f" {len(events)} 个事件")

            print(f"  ✓ URL {url_index} 完成,提取到 {url_events_count} 个事件")

        except Exception as e:
            print(f"  ✗ 处理 URL {url_index} 时出错: {e}")
            import traceback
            traceback.print_exc()
            continue

    print(f"\n{'='*60}")
    print(f"去重前事件数: {len(all_events)}")

    # 去重
    all_events = deduplicate_events(all_events, content_threshold=0.75)
    print(f"去重后事件数: {len(all_events)}")
    print(f"{'='*60}")

    # 输出结果并保存
    print("\n提取的事件:")
    print(json.dumps(all_events, ensure_ascii=False, indent=2))

    with open('extracted_events.json', 'w', encoding='utf-8') as f:
        json.dump(all_events, f, ensure_ascii=False, indent=2)
    print("结果已保存到 extracted_events.json")

if __name__ == "__main__":
    main()