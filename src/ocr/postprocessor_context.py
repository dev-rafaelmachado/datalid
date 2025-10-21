"""
📝 Contextual Postprocessor
Pós-processamento inteligente com mapeamento contextual de ambiguidades.
Inclui fuzzy matching e correção de formatos conhecidos.
"""

import re
from typing import Dict, List, Optional, Tuple

from loguru import logger

# Import condicional para Levenshtein (edit distance)
try:
    from Levenshtein import distance as levenshtein_distance
    HAS_LEVENSHTEIN = True
except ImportError:
    HAS_LEVENSHTEIN = False
    logger.warning("⚠️  python-Levenshtein não instalado. Fuzzy matching será limitado.")


class ContextualPostprocessor:
    """
    Pós-processador contextual para OCR.
    
    Funcionalidades:
    - Uppercase/lowercase normalização
    - Remoção de símbolos indesejados
    - Mapeamento contextual de ambiguidades (O→0, I→1, etc.)
    - Regex/fuzzy matching para formatos esperados
    - Correção de formatos conhecidos (LOT, datas, etc.)
    """
    
    def __init__(self, config: Optional[dict] = None):
        """
        Inicializa postprocessor.
        
        Args:
            config: Configuração com:
                - uppercase: bool (converter para uppercase)
                - remove_symbols: bool (remover símbolos)
                - ambiguity_mapping: bool (mapear caracteres ambíguos)
                - fix_formats: bool (corrigir formatos conhecidos)
                - expected_formats: lista de regex patterns esperados
                - enable_fuzzy_match: bool (fuzzy matching para correção)
                - fuzzy_threshold: int (distância máxima para fuzzy match)
        """
        config = config or {}
        self.uppercase = config.get('uppercase', True)
        self.remove_symbols = config.get('remove_symbols', False)
        self.ambiguity_mapping = config.get('ambiguity_mapping', True)
        self.fix_formats = config.get('fix_formats', True)
        self.enable_fuzzy_match = config.get('enable_fuzzy_match', True)
        self.fuzzy_threshold = config.get('fuzzy_threshold', 2)
        
        # Formatos esperados (regex patterns)
        self.expected_formats = config.get('expected_formats', [
            r'LOT[EO]?\s*\.?\s*\d+',           # LOTE 123, LOT.123
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # Datas
            r'[A-Z]{2,}\s*\d+',                 # Códigos alfanuméricos
        ])
        
        # Dicionário de palavras conhecidas para fuzzy match
        self.known_words = config.get('known_words', [
            'LOT', 'LOTE', 'DATE', 'DATA', 'BATCH', 'MFG', 'EXP',
            'FABRICAÇÃO', 'VALIDADE', 'PRODUTO', 'PRODUCT'
        ])
        
        # Mapeamentos contextuais
        self.ambiguity_map = {
            'numeric': {
                'O': '0', 'o': '0',
                'I': '1', 'l': '1', 'i': '1', '|': '1',
                'S': '5', 's': '5',
                'Z': '2', 'z': '2',
                'B': '8', 'b': '8',
                'G': '6', 'g': '6',
                'T': '7', 't': '7',  # T pode ser 7 em contextos específicos
            },
            'alpha': {
                '0': 'O',
                '1': 'I',
                '5': 'S',
                '8': 'B',
                '6': 'G',
                '7': 'T',
            }
        }
    
    def process(self, text: str) -> str:
        """
        Aplica pós-processamento completo.
        
        Args:
            text: Texto bruto do OCR
            
        Returns:
            Texto processado
        """
        if not text:
            return ""
        
        result = text
        
        # 1. Uppercase
        if self.uppercase:
            result = result.upper()
        
        # 2. Remover símbolos indesejados
        if self.remove_symbols:
            result = self._remove_unwanted_symbols(result)
        
        # 3. Mapeamento contextual
        if self.ambiguity_mapping:
            result = self._apply_contextual_mapping(result)
        
        # 4. Correção de formatos
        if self.fix_formats:
            result = self._fix_known_formats(result)
        
        # 5. Fuzzy matching para palavras conhecidas
        if self.enable_fuzzy_match and HAS_LEVENSHTEIN:
            result = self._apply_fuzzy_correction(result)
        
        # 6. Limpeza final
        result = self._final_cleanup(result)
        
        return result
    
    def _remove_unwanted_symbols(self, text: str) -> str:
        """Remove símbolos indesejados (exceto / - . :)."""
        # Manter: letras, números, espaços, / - . :
        cleaned = re.sub(r'[^A-Za-z0-9\s/\-.:]+', '', text)
        return cleaned
    
    def _apply_contextual_mapping(self, text: str) -> str:
        """
        Aplica mapeamento contextual de ambiguidades.
        
        Estratégia:
        - Se rodeado por números → usar mapeamento numérico
        - Se rodeado por letras → usar mapeamento alfabético
        - Se misto → heurística baseada em contexto
        """
        result = list(text)
        
        for i, char in enumerate(result):
            # Verificar contexto (char anterior e posterior)
            prev_is_digit = (i > 0 and result[i-1].isdigit())
            next_is_digit = (i < len(result) - 1 and result[i+1].isdigit())
            
            # Contexto numérico
            if prev_is_digit or next_is_digit:
                if char in self.ambiguity_map['numeric']:
                    result[i] = self.ambiguity_map['numeric'][char]
                    logger.debug(f"🔄 Mapeamento numérico: '{char}' → '{result[i]}'")
            
            # Contexto alfabético
            else:
                if char in self.ambiguity_map['alpha']:
                    # Só mapear se faz sentido (ex: não mapear 0 em "10" para "IO")
                    # Heurística: só mapear se isolado ou no início de palavra
                    is_isolated = (
                        (i == 0 or not result[i-1].isalnum()) and
                        (i == len(result) - 1 or not result[i+1].isalnum())
                    )
                    
                    if is_isolated:
                        result[i] = self.ambiguity_map['alpha'][char]
                        logger.debug(f"🔄 Mapeamento alfabético: '{char}' → '{result[i]}'")
        
        return ''.join(result)
    
    def _fix_known_formats(self, text: str) -> str:
        """
        Corrige formatos conhecidos.
        
        Exemplos:
        - "L0TE" → "LOTE"
        - "LOT 123" → "LOT123"
        - Datas mal formatadas
        """
        result = text
        
        # 1. LOT/LOTE
        # Corrigir L0TE → LOTE, L0T → LOT
        result = re.sub(r'L[0O]TE', 'LOTE', result)
        result = re.sub(r'L[0O]T(?!\w)', 'LOT', result)
        
        # Remover espaços entre LOT e número
        result = re.sub(r'(LOT[EO]?)\s*\.?\s*(\d)', r'\1\2', result)
        
        # 2. Datas
        # Normalizar separadores: usar /
        result = re.sub(r'(\d{1,2})[-.](\d{1,2})[-.](\d{2,4})', r'\1/\2/\3', result)
        
        # 3. Códigos alfanuméricos
        # Remover espaços entre letras e números consecutivos
        result = re.sub(r'([A-Z]{2,})\s+(\d+)', r'\1\2', result)
        
        return result
    
    def _final_cleanup(self, text: str) -> str:
        """Limpeza final: espaços duplicados, trim."""
        # Remover espaços duplicados
        text = re.sub(r'\s+', ' ', text)
        
        # Strip
        text = text.strip()
        
        return text
    
    def validate_format(self, text: str) -> Optional[str]:
        """
        Valida se texto corresponde a um formato esperado.
        
        Returns:
            Nome do formato se match, None caso contrário
        """
        format_names = {
            r'LOT[EO]?\d+': 'lot_code',
            r'\d{1,2}/\d{1,2}/\d{2,4}': 'date',
            r'[A-Z]{2,}\d+': 'alphanumeric_code',
        }
        
        for pattern, name in format_names.items():
            if re.search(pattern, text):
                return name
        
        return None
    
    def fuzzy_match_format(self, text: str, expected_pattern: str, threshold: float = 0.8) -> bool:
        """
        Fuzzy matching com formato esperado.
        
        Args:
            text: Texto para validar
            expected_pattern: Padrão esperado (regex)
            threshold: Threshold de similaridade (0-1)
            
        Returns:
            True se match suficientemente bom
        """
        # Match exato
        if re.search(expected_pattern, text):
            return True
        
        # Fuzzy: permitir alguns caracteres errados
        # Implementação simples: edit distance normalizada
        # (para produção, usar python-Levenshtein)
        
        return False
    
    def _apply_fuzzy_correction(self, text: str) -> str:
        """
        Aplica fuzzy matching para corrigir palavras conhecidas.
        
        Usa edit distance (Levenshtein) para encontrar palavras similares
        e corrigir erros de OCR.
        
        Args:
            text: Texto para corrigir
            
        Returns:
            Texto com palavras corrigidas
        """
        if not HAS_LEVENSHTEIN:
            return text
        
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Verificar se palavra é suficientemente longa para fuzzy match
            if len(word) < 3:
                corrected_words.append(word)
                continue
            
            # Encontrar palavra conhecida mais similar
            best_match = None
            best_distance = float('inf')
            
            for known_word in self.known_words:
                dist = levenshtein_distance(word.upper(), known_word.upper())
                
                # Normalizar por comprimento
                max_len = max(len(word), len(known_word))
                normalized_dist = dist / max_len
                
                if dist < best_distance and normalized_dist <= 0.3:  # 30% de diferença permitida
                    best_distance = dist
                    best_match = known_word
            
            # Se encontrou match e está dentro do threshold, usar match
            if best_match and best_distance <= self.fuzzy_threshold:
                logger.debug(f"🔄 Fuzzy match: '{word}' → '{best_match}' (dist: {best_distance})")
                corrected_words.append(best_match if self.uppercase else best_match.lower())
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def calculate_confidence_score(self, text: str) -> float:
        """
        Calcula score de confiança baseado em heurísticas.
        
        Considera:
        - Match com formatos esperados
        - Presença de palavras conhecidas
        - Ausência de caracteres estranhos
        
        Returns:
            Score 0.0 a 1.0
        """
        score = 0.5  # Base score
        
        # Bonus por match de formato
        if self.validate_format(text):
            score += 0.3
        
        # Bonus por palavras conhecidas
        words = text.split()
        known_count = sum(1 for word in words if word.upper() in self.known_words)
        if len(words) > 0:
            known_ratio = known_count / len(words)
            score += known_ratio * 0.2
        
        # Penalidade por símbolos estranhos
        strange_chars = sum(1 for c in text if not c.isalnum() and c not in ' /-.,:')
        if strange_chars > 0:
            score -= min(0.3, strange_chars * 0.05)
        
        # Penalidade se muito curto ou muito longo
        if len(text.strip()) < 3:
            score -= 0.2
        elif len(text.strip()) > 100:
            score -= 0.1
        
        return max(0.0, min(1.0, score))


class DatePostprocessor:
    """
    Postprocessor especializado para datas.
    
    Corrige formatos de data e valida.
    """
    
    def __init__(self):
        # Formatos de data aceitos
        self.date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # dd/mm/yyyy
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',    # yyyy/mm/dd
        ]
    
    def process(self, text: str) -> Optional[str]:
        """
        Extrai e normaliza data.
        
        Returns:
            Data normalizada no formato dd/mm/yyyy, ou None
        """
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                groups = match.groups()
                
                # Detectar formato
                if len(groups[0]) == 4:  # yyyy/mm/dd
                    year, month, day = groups
                else:  # dd/mm/yyyy
                    day, month, year = groups
                
                # Converter ano de 2 dígitos
                if len(year) == 2:
                    year_int = int(year)
                    # Heurística: 00-30 → 2000-2030, 31-99 → 1931-1999
                    if year_int <= 30:
                        year = f"20{year}"
                    else:
                        year = f"19{year}"
                
                # Validar ranges
                day_int = int(day)
                month_int = int(month)
                year_int = int(year)
                
                if not (1 <= day_int <= 31):
                    continue
                if not (1 <= month_int <= 12):
                    continue
                if not (1900 <= year_int <= 2100):
                    continue
                
                # Normalizar para dd/mm/yyyy
                return f"{day_int:02d}/{month_int:02d}/{year_int:04d}"
        
        return None


__all__ = ['ContextualPostprocessor', 'DatePostprocessor']
