import json
import sys
import csv

# ファイルパス
WIKIPEDIA_INDEX_CSV = "/home/ubuntu/nlp/corpus/wikipedia_index.csv"
WIKIPEDIA_CSV = "/home/ubuntu/nlp/corpus/wikipedia.csv"

def get_wiki_text(search_title):
    """
    指定したタイトルを検索し、対応するテキストを取得する関数。

    Args:
        search_title (str): 検索するタイトル

    Returns:
        str: 対応するテキスト（存在しない場合は None）
    """
    # フィールドサイズ制限を緩和
    csv.field_size_limit(sys.maxsize)

    # wikipedia_index.csv を検索
    matching_id = None
    try:
        with open(WIKIPEDIA_INDEX_CSV, "r", encoding="utf-8") as index_csv:
            index_reader = csv.DictReader(index_csv)
            for row in index_reader:
                if row["title"] == search_title:
                    matching_id = row["id"]
                    break
    except Exception as e:
        print(f"wikipedia_index.csv の読み込み中にエラーが発生しました: {e}")
        return None

    if matching_id is None:
        print(f"タイトル '{search_title}' は wikipedia_index.csv に見つかりませんでした。")
        return None

    # wikipedia.csv から対応するテキストを取得
    try:
        with open(WIKIPEDIA_CSV, "r", encoding="utf-8") as data_csv:
            data_reader = csv.DictReader(data_csv)
            for row in data_reader:
                if row["id"] == matching_id:
                    # テキストをクリーニングして返す
                    return row["text"].strip()
    except Exception as e:
        print(f"wikipedia.csv の読み込み中にエラーが発生しました: {e}")
        return None

    print(f"ID '{matching_id}' に対応するデータが wikipedia.csv に見つかりませんでした。")
    return None


import tqdm
import MeCab
from concurrent.futures import ProcessPoolExecutor

def process_line(line, conditions):
    """
    単一の行を解析し、条件にマッチする部分を抽出

    Args:
        line (str): テキストの行
        conditions (list): 条件リスト（例: ["横断歩道", ["助詞"]]）

    Returns:
        list: マッチした部分のリスト
    """
    mecab = MeCab.Tagger("-Owakati")
    matches = []
    tokens = []

    # 行を形態素解析してトークン化
    node = mecab.parseToNode(line.strip())
    while node:
        tokens.append({
            "surface": node.surface,
            "feature": node.feature.split(",")[0]  # 最初の品詞を抽出
        })
        node = node.next

    # トークン化された結果で条件を満たす部分をチェック
    for i in range(len(tokens) - len(conditions) + 1):
        match = True
        matched_parts = []  # 条件に一致した部分を格納
        for j, condition in enumerate(conditions):
            if isinstance(condition, str):  # 文字列条件の場合
                # surfaceに一致するか、またはline全体に文字列が含まれるかチェック
                if tokens[i + j]["surface"] == condition or condition in line:
                    matched_parts.append(condition)
                else:
                    match = False
                    break
            elif isinstance(condition, list):  # 品詞条件の場合
                if tokens[i + j]["feature"] in condition:
                    matched_parts.append(tokens[i + j]["surface"])
                else:
                    match = False
                    break

        if match:
            matched_text = "".join(matched_parts)  # 一致した部分を結合
            matches.append(matched_text)

    return matches


def extract_matching_parts_parallel(file_path, conditions, num_workers=4):
    """
    汎用的な形態素解析による条件マッチング

    Args:
        file_path (str): テキストファイルのパス
        conditions (list): 条件リスト（例: ["横断歩道", ["助詞"]]）
        num_workers (int): 並列処理のワーカー数

    Returns:
        list: マッチした部分のリスト
    """
    try:
        # # ファイル行数をカウント
        # with open(file_path, "r", encoding="utf-8") as f:
        #     total_lines = sum(1 for _ in f)

        # 必要な行だけを抽出
        keyword_conditions = [cond for cond in conditions if isinstance(cond, str)]
        with open(file_path, "r", encoding="utf-8") as f:
            filtered_lines = [line for line in f if any(keyword in line for keyword in keyword_conditions)]

        matches = []

        # 並列処理を実行
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            with tqdm(total=len(filtered_lines), desc="Processing") as pbar:
                for result in executor.map(process_line, filtered_lines, [conditions] * len(filtered_lines)):
                    matches.extend(result)
                    pbar.update(1)

        return matches

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return []
