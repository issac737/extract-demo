"""
测试数据抽取脚本
从 finewiki_level1_classified 文件夹中随机抽取测试样本
将抽取的文件和元数据保存到 test_data 文件夹中
这样可以在不同版本之间保持测试数据一致,便于对比评估指标
"""

import os
import json
import glob
import random
import shutil
from collections import defaultdict
from datetime import datetime

def extract_test_data(
    data_folder: str,
    output_folder: str,
    n_per_folder: int = 10,
    seed: int = 42
):
    """
    从数据文件夹中抽取测试样本

    参数:
        data_folder: 源数据文件夹路径
        output_folder: 输出文件夹路径
        n_per_folder: 每个子文件夹抽取的文件数
        seed: 随机种子,保证可重复性
    """
    # 设置随机种子
    random.seed(seed)

    # 创建输出文件夹
    os.makedirs(output_folder, exist_ok=True)

    print(f"\n{'='*80}")
    print(f"测试数据抽取工具")
    print(f"{'='*80}")
    print(f"源文件夹: {data_folder}")
    print(f"输出文件夹: {output_folder}")
    print(f"每个子文件夹抽取: {n_per_folder} 个文件")
    print(f"随机种子: {seed}")
    print(f"{'='*80}\n")

    # 按子文件夹分组
    files_by_folder = defaultdict(list)

    # 获取所有子文件夹
    for subfolder in os.scandir(data_folder):
        if subfolder.is_dir():
            # 获取该文件夹下的所有md文件
            md_files = glob.glob(os.path.join(subfolder.path, "*.md"))
            if md_files:
                files_by_folder[subfolder.name] = md_files

    print(f"找到 {len(files_by_folder)} 个子文件夹")
    print("="*80)

    # 从每个文件夹抽取文件
    selected_files = []
    folder_stats = {}

    for folder_name, md_files in sorted(files_by_folder.items()):
        n_sample = min(n_per_folder, len(md_files))
        selected = random.sample(md_files, n_sample)
        selected_files.extend(selected)

        folder_stats[folder_name] = {
            "total_files": len(md_files),
            "selected_files": n_sample,
            "files": [os.path.basename(f) for f in selected]
        }

        print(f"  {folder_name}: 抽取 {n_sample}/{len(md_files)} 个文件")

    print(f"\n共抽取 {len(selected_files)} 个文件")
    print("="*80)

    # 复制文件到输出文件夹
    print("\n开始复制文件...")
    copied_files = []

    for file_path in selected_files:
        # 保持原有的文件夹结构
        relative_path = os.path.relpath(file_path, data_folder)
        output_path = os.path.join(output_folder, relative_path)

        # 创建目标文件夹
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 复制文件
        shutil.copy2(file_path, output_path)
        copied_files.append({
            "source": file_path,
            "destination": output_path,
            "relative_path": relative_path
        })

    print(f"已复制 {len(copied_files)} 个文件")

    # 生成元数据文件
    metadata = {
        "extraction_date": datetime.now().isoformat(),
        "source_folder": data_folder,
        "output_folder": output_folder,
        "n_per_folder": n_per_folder,
        "random_seed": seed,
        "total_folders": len(files_by_folder),
        "total_files": len(selected_files),
        "folder_stats": folder_stats,
        "file_list": [f["relative_path"] for f in copied_files]
    }

    metadata_path = os.path.join(output_folder, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"\n元数据已保存到: {metadata_path}")
    print(f"{'='*80}")
    print(f"✅ 测试数据抽取完成!")
    print(f"{'='*80}\n")

    return metadata

def list_test_data(output_folder: str):
    """列出已有的测试数据信息"""
    metadata_path = os.path.join(output_folder, "metadata.json")

    if not os.path.exists(metadata_path):
        print(f"❌ 未找到测试数据元数据文件: {metadata_path}")
        return None

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    print(f"\n{'='*80}")
    print(f"测试数据信息")
    print(f"{'='*80}")
    print(f"抽取时间: {metadata['extraction_date']}")
    print(f"源文件夹: {metadata['source_folder']}")
    print(f"输出文件夹: {metadata['output_folder']}")
    print(f"随机种子: {metadata['random_seed']}")
    print(f"总文件夹数: {metadata['total_folders']}")
    print(f"总文件数: {metadata['total_files']}")
    print(f"每个文件夹抽取: {metadata['n_per_folder']} 个文件")
    print(f"{'='*80}\n")

    print("各文件夹统计:")
    for folder_name, stats in sorted(metadata['folder_stats'].items()):
        print(f"  {folder_name}: {stats['selected_files']}/{stats['total_files']} 个文件")

    print(f"\n{'='*80}\n")

    return metadata

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="测试数据抽取工具")
    parser.add_argument(
        "--action",
        choices=["extract", "list"],
        default="extract",
        help="操作类型: extract=抽取新数据, list=查看已有数据"
    )
    parser.add_argument(
        "--data-folder",
        default=r"C:\Users\PC\Desktop\git demo\finewiki_level1_classified",
        help="源数据文件夹路径"
    )
    parser.add_argument(
        "--output-folder",
        default=r"C:\Users\PC\Desktop\git demo\test_data",
        help="输出文件夹路径"
    )
    parser.add_argument(
        "--n-per-folder",
        type=int,
        default=10,
        help="每个子文件夹抽取的文件数"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子"
    )

    args = parser.parse_args()

    if args.action == "extract":
        # 检查输出文件夹是否已存在
        metadata_path = os.path.join(args.output_folder, "metadata.json")
        if os.path.exists(metadata_path):
            response = input(f"\n⚠️  输出文件夹已存在测试数据,是否覆盖? (y/n): ")
            if response.lower() != 'y':
                print("取消操作")
                return
            print("将覆盖已有数据...\n")

        extract_test_data(
            data_folder=args.data_folder,
            output_folder=args.output_folder,
            n_per_folder=args.n_per_folder,
            seed=args.seed
        )

    elif args.action == "list":
        list_test_data(args.output_folder)

if __name__ == "__main__":
    main()
