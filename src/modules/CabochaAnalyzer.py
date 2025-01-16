import CaboCha
import xml.etree.ElementTree as ET


class CabochaAnalyzer:
  
    # Class-level properties
    _sentence = None
    _target = None
    _xml_output = None
    _deps = []

    @classmethod
    def init(cls):
        cls._sentence = None
        cls._target = None
        cls._xml_output = None
        cls._deps = []

    @classmethod
    def set_sentence(cls, sentence):
        """
        Set the sentence to analyze.
        :param sentence: Sentence to analyze.
        """
        cls._sentence = sentence

    @classmethod
    def get_sentence(cls):
        """
        Get the current sentence.
        :return: The current sentence.
        """
        return cls._sentence
    @classmethod
    def get_xml_output(cls):
        return cls._xml_output

    @classmethod
    def get_deps(cls):
        return cls._deps

    @classmethod
    def set_target(cls, target):
        """
        Set the target word to extract dependencies for.
        :param target: Target word.
        """
        cls._target = target

    @classmethod
    def get_target(cls):
        """
        Get the current target word.
        :return: The current target word.
        """
        return cls._target

    @staticmethod
    def parse_sent_to_text(sentence):
        """
        Parse a sentence using CaboCha and return the output text.
        """
        parser = CaboCha.Parser()
        tree = parser.parse(sentence)
        return tree.toString(CaboCha.FORMAT_LATTICE)

    @staticmethod
    def parse_sent_to_xml(sentence):
        """
        Parse a sentence using CaboCha and return the output as XML.
        """
        parser = CaboCha.Parser()
        tree = parser.parse(sentence)
        return tree.toString(CaboCha.FORMAT_XML)

    @classmethod
    def analyze(cls, form="xml"):
        """
        Parse the class's sentence using CaboCha and return the output in the specified format.
        :param form: Output format, either 'text' or 'xml'. Defaults to 'xml'.
        :return: Parsed output in the specified format.
        """
        if cls._sentence is None:
            raise ValueError("Sentence is not set.")

        formats = {
            "text" : CabochaAnalyzer.parse_sent_to_text,
            "xml"  : CabochaAnalyzer.parse_sent_to_xml
        }
       
        cls._xml_output = formats.get(form, lambda *_: None)(cls._sentence)
        
    @classmethod
    def get_dependencies(cls):
        """
        Extract words that depend on the class's target word from CaboCha XML output.
        :param xml_output: The XML output from CaboCha. If not provided, it will parse the current sentence.
        :return: A list of words that depend on the target word.
        """
        if cls._target is None:
            raise ValueError("Target word is not set.")

        if cls._xml_output is None:
            raise ValueError("Xml output is not set")

        root = ET.fromstring(cls._xml_output)
        deps = []

        # Build a mapping of chunk IDs to their tokens
        chunk_to_tokens = {}
        for chunk in root.findall('chunk'):
            chunk_id = chunk.get('id')
            tokens = [tok.text for tok in chunk.findall('tok')]
            chunk_to_tokens[chunk_id] = tokens

        # Find the target chunk
        target_chunk_id = None
        for chunk_id, tokens in chunk_to_tokens.items():
            if cls._target in tokens:
                target_chunk_id = chunk_id
                break

        # If target chunk is found, collect its dependents
        if target_chunk_id is not None:
            for chunk in root.findall('chunk'):
                if chunk.get('link') == target_chunk_id:
                    deps.extend(chunk_to_tokens[chunk.get('id')])

        cls._deps = deps



"""
# Example usage
if __name__ == "__main__":
    # Set the class-level sentence and target
    CabochaAnalyzer.set_sentence("私は手錠をしゃぶしゃぶしました")
    CabochaAnalyzer.set_target("しゃぶしゃぶ")

    # XML形式で解析
    xml_output = CabochaAnalyzer.analyze(form="xml")
    print(xml_output)

    # ターゲット単語にかかる語を取得
    dependencies = CabochaAnalyzer.get_dependencies()
    print(f"Dependencies for '{CabochaAnalyzer.get_target()}': {dependencies}")
"""
