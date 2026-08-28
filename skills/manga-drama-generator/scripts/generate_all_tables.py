#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI动漫制作素材生成器 - 主入口脚本
用于一键生成人物信息表、场景信息表、分镜信息表

使用方式：
1. 使用JSON文件：
   python generate_all_tables.py --characters characters.json --scenes scenes.json --storyboards storyboards.json --output-dir ./output

2. 使用JSON字符串（适合脚本调用）：
   python generate_all_tables.py --characters-data '<JSON>' --scenes-data '<JSON>' --storyboards-data '<JSON>'

3. 作为模块导入：
   from generate_all_tables import generate_all_tables
   generate_all_tables(characters, scenes, storyboards, output_dir)
"""

import argparse
import json
import os
import sys

# 导入子模块
from generate_character_table import create_character_table
from generate_scene_table import create_scene_table
from generate_storyboard_table import create_storyboard_table


def generate_all_tables(
    characters: list = None,
    scenes: list = None,
    storyboards: list = None,
    output_dir: str = ".",
    project_name: str = ""
) -> dict:
    """
    一键生成所有表格
    
    Args:
        characters: 人物数据列表
        scenes: 场景数据列表
        storyboards: 分镜数据列表
        output_dir: 输出目录
        project_name: 项目名称前缀（可选）
    
    Returns:
        dict: 包含生成的文件路径
    """
    results = {}
    
    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 文件名前缀
    prefix = f"{project_name}_" if project_name else ""
    
    # 生成人物信息表
    if characters:
        output_path = os.path.join(output_dir, f"{prefix}人物信息表.xlsx")
        create_character_table(characters, output_path)
        results["characters"] = {
            "path": output_path,
            "count": len(characters)
        }
        print(f"✅ 人物信息表已生成：{output_path}（{len(characters)} 个角色）")
    
    # 生成场景信息表
    if scenes:
        output_path = os.path.join(output_dir, f"{prefix}场景信息表.xlsx")
        create_scene_table(scenes, output_path)
        results["scenes"] = {
            "path": output_path,
            "count": len(scenes)
        }
        print(f"✅ 场景信息表已生成：{output_path}（{len(scenes)} 个场景）")
    
    # 生成分镜信息表
    if storyboards:
        output_path = os.path.join(output_dir, f"{prefix}分镜信息表.xlsx")
        create_storyboard_table(storyboards, output_path)
        episodes = set(s.get("episode", 1) for s in storyboards)
        results["storyboards"] = {
            "path": output_path,
            "count": len(storyboards),
            "episodes": len(episodes)
        }
        print(f"✅ 分镜信息表已生成：{output_path}（{len(episodes)} 集，{len(storyboards)} 个分镜）")
    
    return results


def load_json_data(data_str: str = None, file_path: str = None) -> list:
    """
    从字符串或文件加载JSON数据
    """
    if data_str:
        return json.loads(data_str)
    elif file_path:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def main():
    parser = argparse.ArgumentParser(
        description='AI动漫制作素材生成器 - 一键生成所有表格',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 使用JSON文件
  python generate_all_tables.py --characters characters.json --scenes scenes.json --storyboards storyboards.json
  
  # 指定输出目录和项目名称
  python generate_all_tables.py --characters characters.json --output-dir ./output --project-name "我的项目"
  
  # 只生成部分表格
  python generate_all_tables.py --characters characters.json  # 只生成人物表
        '''
    )
    
    # 人物数据输入
    char_group = parser.add_mutually_exclusive_group()
    char_group.add_argument('--characters', type=str, help='人物数据JSON文件路径')
    char_group.add_argument('--characters-data', type=str, help='人物数据JSON字符串')
    
    # 场景数据输入
    scene_group = parser.add_mutually_exclusive_group()
    scene_group.add_argument('--scenes', type=str, help='场景数据JSON文件路径')
    scene_group.add_argument('--scenes-data', type=str, help='场景数据JSON字符串')
    
    # 分镜数据输入
    story_group = parser.add_mutually_exclusive_group()
    story_group.add_argument('--storyboards', type=str, help='分镜数据JSON文件路径')
    story_group.add_argument('--storyboards-data', type=str, help='分镜数据JSON字符串')
    
    # 输出选项
    parser.add_argument('--output-dir', type=str, default='.', help='输出目录（默认：当前目录）')
    parser.add_argument('--project-name', type=str, default='', help='项目名称前缀（可选）')
    
    args = parser.parse_args()
    
    # 检查是否有任何输入
    if not any([args.characters, args.characters_data, 
                args.scenes, args.scenes_data,
                args.storyboards, args.storyboards_data]):
        parser.print_help()
        print("\n错误：请至少提供一种数据输入", file=sys.stderr)
        sys.exit(1)
    
    try:
        # 加载数据
        characters = load_json_data(args.characters_data, args.characters)
        scenes = load_json_data(args.scenes_data, args.scenes)
        storyboards = load_json_data(args.storyboards_data, args.storyboards)
        
        # 生成表格
        print("=" * 60)
        print("AI动漫制作素材生成器")
        print("=" * 60)
        
        results = generate_all_tables(
            characters=characters,
            scenes=scenes,
            storyboards=storyboards,
            output_dir=args.output_dir,
            project_name=args.project_name
        )
        
        print("=" * 60)
        print(f"✅ 生成完成！共 {len(results)} 个表格")
        print("=" * 60)
        
    except json.JSONDecodeError as e:
        print(f"错误：JSON解析失败 - {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"错误：文件不存在 - {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
