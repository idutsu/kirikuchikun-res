import re

def split_text_into_sentences(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile:
        for line in infile:
            sentences = re.split(r'(?<=[。！？\?])', line)  # 文末の句読点で分割
            for sentence in sentences:
                if sentence.strip():  # 空行を除外
                    outfile.write(sentence.strip() + '\n')

