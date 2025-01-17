import CaboCha
import xml.etree.ElementTree as ET


class CabochaAnalyzer:
    
    @staticmethod
    def parse_to_text(sentence):
        """
        Parse a sentence using CaboCha and return the output text.
        """
        parser = CaboCha.Parser()
        tree = parser.parse(sentence)
        return tree.toString(CaboCha.FORMAT_LATTICE)

    @staticmethod
    def parse_to_xml(sentence):
        """
        Parse a sentence using CaboCha and return the output as XML.
        """
        parser = CaboCha.Parser()
        tree = parser.parse(sentence)
        return tree.toString(CaboCha.FORMAT_XML)

    @staticmethod
    def get_deps(xml_output, target):
        root = ET.fromstring(xml_output)
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
            if target in tokens:
                target_chunk_id = chunk_id
                break

        # If target chunk is found, collect its dependents
        if target_chunk_id is not None:
            for chunk in root.findall('chunk'):
                if chunk.get('link') == target_chunk_id:
                    deps.extend(chunk_to_tokens[chunk.get('id')])

        return deps

    @staticmethod
    def get_dependents(target_word, xml_output):
        """
        Get all dependent words for a given target word from CaboCha XML output.
        :param target_word: The word whose dependents are to be found.
        :param xml_output: The XML output from CaboCha. If not provided, it will parse the current sentence.
        :return: A list of words that are dependent on the target word.
        """
        root = ET.fromstring(xml_output)
        dependents = []

        # Find the chunk ID of the target word
        target_chunk_id = None
        for chunk in root.findall('chunk'):
            tokens = [tok.text for tok in chunk.findall('tok')]
            if target_word in tokens:
                target_chunk_id = chunk.get('id')
                break

        if target_chunk_id is None:
            raise ValueError(f"Target word '{target_word}' not found in the sentence.")

        # Find all chunks that link to the target chunk
        for chunk in root.findall('chunk'):
            if chunk.get('link') == target_chunk_id:
                dependent_tokens = [tok.text for tok in chunk.findall('tok')]
                dependents.extend(dependent_tokens)

        return dependents





