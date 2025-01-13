import csv
import spacy
import ginza
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
from sudachipy import dictionary, tokenizer
from spacy.tokens import Doc
from constants import WIKIPEDIA_TEXT, WIKIPEDIA_SENT_TEXT, WIKIPEDIA_TEST_TEXT


class CustomSudachiTokenizer:
    def __init__(self, nlp, split_mode="C"):
        self.nlp = nlp
        self.split_mode_mapping = {
            "A": tokenizer.Tokenizer.SplitMode.A,
            "B": tokenizer.Tokenizer.SplitMode.B,
            "C": tokenizer.Tokenizer.SplitMode.C,
        }
        self.split_mode = self.split_mode_mapping.get(split_mode, tokenizer.Tokenizer.SplitMode.C)
        self.sudachi_tokenizer = dictionary.Dictionary(dict="full").create(mode=self.split_mode)

    def __call__(self, text):
        words = [m.dictionary_form() for m in self.sudachi_tokenizer.tokenize(text)]
        spaces = [True] * len(words)
        return Doc(self.nlp.vocab, words=words, spaces=spaces)

    def keyword_in_dictionary(self, keyword):
        """
        単語が辞書に存在するかを確認する
        Args:
            keyword (str): 確認する単語
        Returns:
            bool: 辞書に存在すればTrue、それ以外はFalse
        """
        tokens = self.sudachi_tokenizer.tokenize(keyword)
        return any(m.dictionary_form() == keyword for m in tokens)

def init_ginza_with_sudachi(split_mode="C"):
    """
    Ginzaモデルを初期化し、Sudachiのトークナイザーを設定
    Returns:
        nlp: Ginzaモデルオブジェクト
    """
    nlp = spacy.load("ja_ginza")
    nlp.tokenizer = CustomSudachiTokenizer(nlp, split_mode)
    return nlp

def process_line_with_ginza_wrapper(args):
    """
    並列処理用のラッパー関数
    Args:
        args (tuple): (line, keyword) のタプル
    Returns:
        list: キーワードに係る単語のリスト。
    """
    line, keyword = args
    return process_line_with_ginza(line, keyword)


def process_line_with_ginza(line, keyword):
    """
    単一の行を解析し、キーワードに係る単語を抽出する
    Args:
        line (str): テキストの行
        keyword (str): キーワード
    Returns:
        dict: キーワードに係る単語のディクショナリー
    """
    matches = {}
    matches["verb"] = []
    matches["adj"] = []

    try:
        # spacy ginza を用いて形態素解析
        doc = nlp(line.strip())

        for sent in doc.sents:  # 文単位で処理
            for token in sent:
                if token.text == keyword or token.lemma_ == keyword:
                    # キーワードを目的語とする動詞を探索
                    if token.dep_ == "obj" and token.head.pos_ == "VERB":
                        matches["verb"].append(token.head.text)
                    # キーワードを主語とする動詞および形容詞を探索
                    if token.dep_ == "nsubj" and (token.head.pos_ == "VERB" or token.head.pos_ == "ADJ"):
                        if token.head.pos_ == "VERB":     
                            matches["verb"].append(token.head.text) 
                        if token.head.pos_ == "ADJ":     
                            matches["adj"].append(token.head.text)
                    for child in token.children: 
                        # キーワードを修飾する形容詞を探索
                        if child.dep_ in {"amod", "advmod", "acl", "advcl"} and child.pos_ == "ADJ":
                            matches["adj"].append(child.text)
                        # キーワードを修飾する動詞を探索
                        if child.dep_ in { "acl", "relcl"} and child.pos_ == "VERB":
                            matches["verb"].append(child.text)
    except Exception as e:
        print(f"Error processing line: {e}")
    return matches

def extract_dependency_words(input_path, output_path, keyword, num_workers=4):
    """
    指定したキーワードを目的語とする動詞および修飾する形容詞を大規模なテキストから抽出。
    Args:
        input_path (str): テキストファイルのパス。
        output_path(str): 結果出力csvのパス。
        keyword (str): 抽出対象のキーワード。
        num_workers (int): 並列処理のワーカー数。
    Returns:
        list: キーワードを目的語とする動詞および修飾する形容詞のリスト。
    """
    try:
        # キーワードが辞書に存在するか確認
        if not nlp.tokenizer.keyword_in_dictionary(keyword):
            print(f"キーワード '{keyword}' は辞書に存在しません。")
            return []
        
        # 必要な行だけを抽出
        with open(input_path, "r", encoding="utf-8") as f:
            filtered_lines = [line for line in f if keyword in line]

        # 結果書き出し
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Word", "Type"])  

            # 並列処理を実行
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                with tqdm(total=len(filtered_lines), desc="Processing") as pbar:
                    results = executor.map(
                        process_line_with_ginza_wrapper, [(line, keyword) for line in filtered_lines]
                    )
                    for result in results:
                        for key, values in result.items():
                            for value in values:
                                writer.writerow([value, key])
                        pbar.update(1)
        print(f"結果を保存しました")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return []

# Ginzaモデルをロード
nlp = init_ginza_with_sudachi(split_mode="C")

# 使用例
if __name__ == "__main__":

    output_path = "/home/ubuntu/nlp/tmp_result.csv" # 出力パス 
    keyword     = "横断歩道"  # 抽出対象のキーワード

    extract_dependency_words(WIKIPEDIA_SENT_TEXT, output_path, keyword)
