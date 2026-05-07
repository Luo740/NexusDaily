import os
from datetime import datetime


def stitch_project(project_root, output_file="project_snapshot.txt"):
    """
    将项目中的所有 .py 脚本拼接成一个 txt 文件。
    排除无关目录，并在开头添加架构说明。
    """
    # 定义需要包含和排除的规则
    included_extensions = ('.py', '.md', '.json')
    excluded_dirs = {'.venv', '.git', '__pycache__', 'data', '.idea', '.vscode'}
    excluded_files = {output_file, 'project_stitcher.py', 'test.py', 'gemini_test.py'}

    # 1. 准备项目概览信息
    project_summary = f"""# 全项目代码快照
# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(project_summary)

        # 2. 递归遍历目录
        for root, dirs, files in os.walk(project_root):
            # 过滤排除目录
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            for file in sorted(files):
                if file.endswith(included_extensions) and file not in excluded_files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, project_root)

                    out.write(f"\n{'─' * 60}\n")
                    out.write(f"📄 {relative_path}\n")
                    out.write(f"{'─' * 60}\n\n")

                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            out.write(content)
                    except Exception as e:
                        out.write(f"Error reading file: {e}")

                    out.write("\n")

    print(f"✅ 项目代码已拼接至: {output_file}")


if __name__ == "__main__":
    # 假设脚本在项目根目录下运行
    current_dir = os.getcwd()
    stitch_project(current_dir)