#!/usr/bin/env python3
"""
批量翻译 skills 目录下的 SKILL.md 文件为中文
"""

import os
import glob
import json

SKILLS_DIR = "/Users/liangyingjie/Documents/my_agent_project/hermes-agent/skills"

def find_skill_files():
    """查找所有 SKILL.md 文件"""
    files = []
    for root, dirs, filenames in os.walk(SKILLS_DIR):
        for filename in filenames:
            if filename == "SKILL.md":
                filepath = os.path.join(root, filename)
                files.append(filepath)
    return sorted(files)

def get_output_path(skill_file):
    """获取输出文件路径"""
    dir_name = os.path.basename(os.path.dirname(skill_file))
    output_path = os.path.join(os.path.dirname(skill_file), f"{dir_name}_SKILL.md")
    return output_path

def main():
    skill_files = find_skill_files()
    print(f"找到 {len(skill_files)} 个 SKILL.md 文件:")
    for f in skill_files:
        rel_path = os.path.relpath(f, SKILLS_DIR)
        output = get_output_path(f)
        print(f"  {rel_path}")
        print(f"    -> {os.path.basename(output)}")

if __name__ == "__main__":
    main()
