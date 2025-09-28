"""Dataset loading and parsing module"""

import json
import os
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class QAItem:
    """Data class for question-answer items"""
    arquivo: str
    titulo: str
    pergunta: str
    esperado: str  # 'Verdadeiro' or 'Falso'
    idx_local: int


class DatasetLoader:
    """Handles dataset loading and parsing"""
    
    @staticmethod
    def load_dataset(path: str) -> List[QAItem]:
        """
        Load dataset from JSON file
        
        Args:
            path: Path to the JSON file
            
        Returns:
            List of QAItem objects
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Arquivo não encontrado: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        items: List[QAItem] = []
        for bloco in data:
            arquivo = bloco.get("arquivo", "")
            titulo = bloco.get("titulo", "")
            perguntas = bloco.get("perguntas", [])
            
            # Process questions in pairs (True, False)
            for i in range(0, len(perguntas) - 1, 2):
                items.append(QAItem(
                    arquivo=arquivo,
                    titulo=titulo,
                    pergunta=perguntas[i],
                    esperado="Verdadeiro",
                    idx_local=i
                ))
                items.append(QAItem(
                    arquivo=arquivo,
                    titulo=titulo,
                    pergunta=perguntas[i + 1],
                    esperado="Falso",
                    idx_local=i + 1
                ))
        
        return items


class ResponseParser:
    """Handles response parsing and label extraction"""
    
    VER_REGEX = re.compile(r"\b(verdadeiro|falso)\b", re.IGNORECASE)
    
    @classmethod
    def parse_label_from_response(cls, text: str) -> Optional[str]:
        """
        Extract Verdadeiro/Falso label from response text
        
        Args:
            text: Response text from the model
            
        Returns:
            'Verdadeiro', 'Falso', or None if not found
        """
        matches = list(cls.VER_REGEX.finditer(text or ""))
        if not matches:
            return None
        
        # Get the last match (reading from the end)
        last = matches[-1].group(1).strip().lower()
        return "Verdadeiro" if last.startswith("v") else "Falso"
    
    @classmethod
    def validate_response(cls, response: str, expected: str) -> Tuple[Optional[str], bool]:
        """
        Validate a response against expected value
        
        Args:
            response: Model response text
            expected: Expected answer ('Verdadeiro' or 'Falso')
            
        Returns:
            Tuple of (predicted_label, is_correct)
        """
        predicted = cls.parse_label_from_response(response)
        is_correct = predicted == expected if predicted else False
        return predicted, is_correct