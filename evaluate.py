"""
实体抽取评估脚本
实现5个评估指标:
1. 覆盖率 - 每条事件平均能抽出多少实体
2. 空抽率 - entities 为空的比例
3. 类型模糊率 - entity.type 被标为 "other / 不确定" 的比例
4. 一致性 - 同一文本多次提取对比
5. 类型频率分布 - 统计各类型的频率
"""

import json
import os
from collections import defaultdict, Counter
from typing import List, Dict
import glob
from entity_types import get_all_entity_types, get_entity_type_mapping


class EntityEvaluator:
    """实体抽取评估器"""

    def __init__(self, events_data: List[Dict]):
        """
        初始化评估器
        Args:
            events_data: 提取的事件数据列表
        """
        self.events = events_data
        self.entity_types = get_all_entity_types()
        self.type_mapping = get_entity_type_mapping()

    def calculate_coverage(self) -> Dict:
        """
        指标1: 覆盖率 - 每条事件平均能抽出多少实体
        Returns:
            {
                "total_events": 总事件数,
                "total_entities": 总实体数,
                "avg_entities_per_event": 平均每事件实体数,
                "max_entities": 最多实体数,
                "min_entities": 最少实体数
            }
        """
        if not self.events:
            return {
                "total_events": 0,
                "total_entities": 0,
                "avg_entities_per_event": 0,
                "max_entities": 0,
                "min_entities": 0
            }

        entity_counts = []
        total_entities = 0

        for event in self.events:
            entities = event.get("entities", [])
            count = len(entities)
            entity_counts.append(count)
            total_entities += count

        return {
            "total_events": len(self.events),
            "total_entities": total_entities,
            "avg_entities_per_event": round(total_entities / len(self.events), 2),
            "max_entities": max(entity_counts) if entity_counts else 0,
            "min_entities": min(entity_counts) if entity_counts else 0,
            "median_entities": sorted(entity_counts)[len(entity_counts) // 2] if entity_counts else 0
        }

    def calculate_empty_rate(self) -> Dict:
        """
        指标2: 空抽率 - entities 为空的比例
        Returns:
            {
                "total_events": 总事件数,
                "empty_events": 空实体事件数,
                "empty_rate": 空抽率 (0-1)
            }
        """
        if not self.events:
            return {
                "total_events": 0,
                "empty_events": 0,
                "empty_rate": 0
            }

        empty_count = 0
        for event in self.events:
            entities = event.get("entities", [])
            if not entities or len(entities) == 0:
                empty_count += 1

        return {
            "total_events": len(self.events),
            "empty_events": empty_count,
            "empty_rate": round(empty_count / len(self.events), 4)
        }

    def calculate_ambiguity_rate(self) -> Dict:
        """
        指标3: 类型模糊率 - entity.type 被标为 "other / 不确定 / unknown" 的比例
        Returns:
            {
                "total_entities": 总实体数,
                "ambiguous_entities": 模糊类型实体数,
                "ambiguity_rate": 模糊率 (0-1),
                "ambiguous_samples": 模糊实体示例
            }
        """
        ambiguous_keywords = ["other", "不确定", "unknown", "其他", "未知"]
        total_entities = 0
        ambiguous_count = 0
        ambiguous_samples = []

        for event in self.events:
            entities = event.get("entities", [])
            for entity in entities:
                total_entities += 1
                entity_type = entity.get("type", "").lower()

                # 检查是否为模糊类型
                is_ambiguous = any(kw in entity_type for kw in ambiguous_keywords)

                if is_ambiguous:
                    ambiguous_count += 1
                    if len(ambiguous_samples) < 10:  # 只收集前10个示例
                        ambiguous_samples.append({
                            "name": entity.get("name", ""),
                            "type": entity.get("type", ""),
                            "description": entity.get("description", "")
                        })

        return {
            "total_entities": total_entities,
            "ambiguous_entities": ambiguous_count,
            "ambiguity_rate": round(ambiguous_count / total_entities, 4) if total_entities > 0 else 0,
            "ambiguous_samples": ambiguous_samples[:10]
        }

    def calculate_type_distribution(self) -> Dict:
        """
        指标5: 类型频率分布
        Returns:
            {
                "type_counts": {type: count},
                "type_percentages": {type: percentage},
                "top_types": 前10个高频类型,
                "rare_types": 低频类型 (出现次数 < 总数的1%)
            }
        """
        type_counter = Counter()
        total_entities = 0

        for event in self.events:
            entities = event.get("entities", [])
            for entity in entities:
                entity_type = entity.get("type", "unknown")
                type_counter[entity_type] += 1
                total_entities += 1

        # 计算百分比
        type_percentages = {}
        for type_name, count in type_counter.items():
            type_percentages[type_name] = round(count / total_entities * 100, 2) if total_entities > 0 else 0

        # 找出低频类型 (< 1%)
        threshold = total_entities * 0.01
        rare_types = {t: c for t, c in type_counter.items() if c < threshold}

        # 找出未使用的定义类型
        used_types = set(type_counter.keys())
        defined_types = set(self.entity_types)
        unused_types = defined_types - used_types

        return {
            "type_counts": dict(type_counter.most_common()),
            "type_percentages": type_percentages,
            "top_types": dict(type_counter.most_common(10)),
            "rare_types": rare_types,
            "unused_types": list(unused_types),
            "total_unique_types": len(type_counter)
        }

    def generate_report(self) -> str:
        """生成完整的评估报告"""
        coverage = self.calculate_coverage()
        empty_rate = self.calculate_empty_rate()
        ambiguity = self.calculate_ambiguity_rate()
        distribution = self.calculate_type_distribution()

        report = []
        report.append("=" * 80)
        report.append("实体抽取评估报告")
        report.append("=" * 80)

        # 指标1: 覆盖率
        report.append("\n【指标1】覆盖率 - 每条事件平均实体数")
        report.append("-" * 80)
        report.append(f"总事件数: {coverage['total_events']}")
        report.append(f"总实体数: {coverage['total_entities']}")
        report.append(f"平均每事件实体数: {coverage['avg_entities_per_event']}")
        report.append(f"中位数: {coverage['median_entities']}")
        report.append(f"最大值: {coverage['max_entities']}")
        report.append(f"最小值: {coverage['min_entities']}")

        # 指标2: 空抽率
        report.append("\n【指标2】空抽率")
        report.append("-" * 80)
        report.append(f"空实体事件数: {empty_rate['empty_events']}")
        report.append(f"空抽率: {empty_rate['empty_rate']:.2%}")
        if empty_rate['empty_rate'] > 0.15:
            report.append("⚠️  警告: 空抽率过高 (>15%), 建议检查提示词或文本质量")

        # 指标3: 类型模糊率
        report.append("\n【指标3】类型模糊率")
        report.append("-" * 80)
        report.append(f"总实体数: {ambiguity['total_entities']}")
        report.append(f"模糊类型实体数: {ambiguity['ambiguous_entities']}")
        report.append(f"类型模糊率: {ambiguity['ambiguity_rate']:.2%}")
        if ambiguity['ambiguity_rate'] > 0.05:
            report.append("⚠️  警告: 类型模糊率过高 (>5%), 建议优化实体类型定义")
        if ambiguity['ambiguous_samples']:
            report.append("\n模糊类型示例:")
            for i, sample in enumerate(ambiguity['ambiguous_samples'][:5], 1):
                report.append(f"  {i}. {sample['name']} ({sample['type']}) - {sample['description']}")

        # 指标5: 类型分布
        report.append("\n【指标5】类型频率分布")
        report.append("-" * 80)
        report.append(f"使用的类型总数: {distribution['total_unique_types']}")
        report.append(f"未使用的定义类型: {len(distribution['unused_types'])}")

        report.append("\n前10高频类型:")
        for type_name, count in list(distribution['top_types'].items())[:10]:
            pct = distribution['type_percentages'].get(type_name, 0)
            type_cn = self.type_mapping.get(type_name, type_name)
            report.append(f"  {type_name:20s} ({type_cn:10s}): {count:6d} 次 ({pct:5.2f}%)")

        if distribution['rare_types']:
            report.append(f"\n低频类型 (<1%, 共{len(distribution['rare_types'])}个):")
            for type_name, count in list(distribution['rare_types'].items())[:10]:
                type_cn = self.type_mapping.get(type_name, type_name)
                report.append(f"  {type_name:20s} ({type_cn:10s}): {count:6d} 次")

        if distribution['unused_types']:
            report.append(f"\n未使用的定义类型 (共{len(distribution['unused_types'])}个):")
            report.append(f"  {', '.join(distribution['unused_types'])}")
            report.append("💡 建议: 考虑删除或合并这些类型")

        report.append("\n" + "=" * 80)
        report.append("评估完成")
        report.append("=" * 80)

        return "\n".join(report)


def calculate_consistency(file_path: str, num_runs: int = 3) -> Dict:
    """
    指标4: 一致性评估 - 同一文本多次提取对比

    Args:
        file_path: 测试文件路径
        num_runs: 提取次数
    Returns:
        一致性统计
    """
    try:
        from main import read_document, segment_into_slices, extract_events_from_slice
    except ImportError:
        return {
            "error": "无法导入 main.py 中的函数,跳过一致性测试",
            "num_runs": 0,
            "total_unique_entities": 0,
            "inconsistent_entities": 0,
            "consistency_rate": 0,
            "inconsistent_samples": []
        }

    print(f"\n正在进行一致性测试 (共{num_runs}次提取)...")

    # 读取文件并分片
    content = read_document(file_path)
    slices = segment_into_slices(content)

    if not slices:
        return {"error": "无法生成切片"}

    # 只测试第一个切片
    test_slice = slices[0]
    all_runs = []

    for run in range(num_runs):
        print(f"  第 {run + 1}/{num_runs} 次提取...", end="", flush=True)
        events = extract_events_from_slice(test_slice, f"consistency_test_{run}")
        all_runs.append(events)
        print(f" 提取到 {len(events)} 个事件")

    # 比较一致性
    entity_type_consistency = []

    for i, events in enumerate(all_runs):
        for event in events:
            entities = event.get("entities", [])
            for entity in entities:
                entity_type_consistency.append({
                    "run": i + 1,
                    "name": entity.get("name", ""),
                    "type": entity.get("type", "")
                })

    # 统计同一实体的类型一致性
    entity_types_map = defaultdict(list)
    for record in entity_type_consistency:
        entity_types_map[record["name"]].append(record["type"])

    inconsistent_entities = []
    for name, types in entity_types_map.items():
        unique_types = set(types)
        if len(unique_types) > 1:
            inconsistent_entities.append({
                "entity_name": name,
                "types": list(unique_types),
                "counts": dict(Counter(types))
            })

    total_unique_entities = len(entity_types_map)
    consistent_rate = 1 - (len(inconsistent_entities) / total_unique_entities) if total_unique_entities > 0 else 0

    return {
        "num_runs": num_runs,
        "total_unique_entities": total_unique_entities,
        "inconsistent_entities": len(inconsistent_entities),
        "consistency_rate": round(consistent_rate, 4),
        "inconsistent_samples": inconsistent_entities[:10]
    }


def main():
    """主函数"""
    import argparse
    import sys

    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

    parser = argparse.ArgumentParser(description="实体抽取评估工具")
    parser.add_argument("--input", default="extracted_events.json", help="提取结果JSON文件路径")
    parser.add_argument("--consistency-test", help="一致性测试的MD文件路径")
    parser.add_argument("--consistency-runs", type=int, default=3, help="一致性测试次数")
    parser.add_argument("--output", default="evaluation_report.txt", help="评估报告输出路径")

    args = parser.parse_args()

    # 读取提取结果
    if not os.path.exists(args.input):
        print(f"错误: 找不到文件 {args.input}")
        return

    with open(args.input, 'r', encoding='utf-8') as f:
        events = json.load(f)

    print(f"\n已加载 {len(events)} 个事件")

    # 创建评估器
    evaluator = EntityEvaluator(events)

    # 生成基础报告
    report = evaluator.generate_report()
    print(report)

    # 一致性测试
    if args.consistency_test:
        if os.path.exists(args.consistency_test):
            consistency_result = calculate_consistency(
                args.consistency_test,
                num_runs=args.consistency_runs
            )

            consistency_report = [
                "\n" + "=" * 80,
                "【指标4】一致性评估",
                "=" * 80,
                f"测试次数: {consistency_result['num_runs']}",
                f"唯一实体总数: {consistency_result['total_unique_entities']}",
                f"类型不一致实体数: {consistency_result['inconsistent_entities']}",
                f"一致性率: {consistency_result['consistency_rate']:.2%}",
            ]

            if consistency_result['inconsistent_samples']:
                consistency_report.append("\n类型不一致示例:")
                for sample in consistency_result['inconsistent_samples'][:5]:
                    consistency_report.append(f"  实体: {sample['entity_name']}")
                    consistency_report.append(f"  不同类型: {sample['types']}")
                    consistency_report.append(f"  出现次数: {sample['counts']}")
                    consistency_report.append("")

            consistency_report.append("=" * 80)
            consistency_text = "\n".join(consistency_report)
            print(consistency_text)
            report += "\n" + consistency_text
        else:
            print(f"一致性测试文件不存在: {args.consistency_test}")

    # 保存报告
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n评估报告已保存到: {args.output}")


if __name__ == "__main__":
    main()
