import re


def normalize_wordlist(input_file, output_file, sort_words=False, to_lower=False):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    words = []
    for line in lines:
        # 去除首尾空格和换行符
        line = line.strip()
        if not line:
            continue

        # 按空白字符拆分（适用于空格、多个空格、Tab 等分隔的情况）
        parts = re.split(r'\s+', line)
        for part in parts:
            if part:
                if to_lower:
                    part = part.lower()
                words.append(part)

    # 可选：去重并排序
    if sort_words:
        words = sorted(set(words))

    # 写入输出文件
    with open(output_file, 'w', encoding='utf-8') as f:
        for word in words:
            f.write(word + '\n')

    print(f"处理完成！共 {len(words)} 个单词，已保存到 {output_file}")


# 使用示例
normalize_wordlist('vocabulary.txt', 'vocabulary.txt', sort_words=False, to_lower=False)