"""
📅 Pós-processadores de Texto OCR
Parse e validação de datas extraídas.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


class DateParser:
    """Parser e validador de datas."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Inicializa o parser de datas.
        
        Args:
            config: Configuração de parsing
        """
        self.config = config or {}
        self.date_formats = self.config.get('date_formats', [
            '%d/%m/%Y',
            '%d/%m/%y',
            '%d.%m.%Y',
            '%d-%m-%Y',
            '%d %m %Y',
            '%d%m%Y'
        ])
        
        validation = self.config.get('validation', {})
        self.min_year = validation.get('min_year', 2024)
        self.max_year = validation.get('max_year', 2035)
        self.allow_past = validation.get('allow_past', False)
        
        corrections = self.config.get('corrections', {})
        self.apply_corrections = corrections.get('enabled', True)
        self.common_errors = corrections.get('common_errors', {
            'O': '0', 'o': '0',
            'I': '1', 'l': '1',
            'S': '5', 'B': '8',
            'Z': '2', 'G': '6'
        })
    
    def parse(self, text: str) -> Tuple[Optional[datetime], float]:
        """
        Faz parse do texto para extrair data.
        
        Args:
            text: Texto extraído pelo OCR
            
        Returns:
            Tupla (data, confiança)
        """
        if not text or text.strip() == '':
            return None, 0.0
        
        # Limpar texto
        text = text.strip()
        
        # Aplicar correções de OCR
        if self.apply_corrections:
            text = self._apply_ocr_corrections(text)
        
        # Tentar extrair data com regex
        date_candidates = self._extract_date_candidates(text)
        
        if not date_candidates:
            logger.debug(f"📅 Nenhuma data encontrada em: '{text}'")
            return None, 0.0
        
        # Tentar fazer parse de cada candidata
        for candidate in date_candidates:
            parsed_date, confidence = self._try_parse_date(candidate)
            if parsed_date:
                # Validar data
                if self._validate_date(parsed_date):
                    logger.debug(f"✅ Data válida: {parsed_date.strftime('%d/%m/%Y')} (conf: {confidence:.2f})")
                    return parsed_date, confidence
                else:
                    logger.debug(f"❌ Data inválida: {parsed_date.strftime('%d/%m/%Y')}")
        
        return None, 0.0
    
    def _apply_ocr_corrections(self, text: str) -> str:
        """Corrige erros comuns de OCR."""
        corrected = text
        for wrong, correct in self.common_errors.items():
            corrected = corrected.replace(wrong, correct)
        
        if corrected != text:
            logger.debug(f"🔧 Correções aplicadas: '{text}' → '{corrected}'")
        
        return corrected
    
    def _extract_date_candidates(self, text: str) -> List[str]:
        """Extrai candidatas a data usando regex."""
        patterns = [
            r'\b\d{1,2}[/.\-\s]\d{1,2}[/.\-\s]\d{4}\b',  # DD/MM/YYYY
            r'\b\d{1,2}[/.\-\s]\d{1,2}[/.\-\s]\d{2}\b',  # DD/MM/YY
            r'\b\d{8}\b',  # DDMMYYYY
        ]
        
        candidates = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            candidates.extend(matches)
        
        return candidates
    
    def _try_parse_date(self, date_str: str) -> Tuple[Optional[datetime], float]:
        """Tenta fazer parse da data com múltiplos formatos."""
        # Normalizar separadores
        normalized = date_str.replace('.', '/').replace('-', '/').replace(' ', '/')
        
        for fmt in self.date_formats:
            try:
                parsed_date = datetime.strptime(normalized, fmt)
                
                # Se ano de 2 dígitos, ajustar para século correto
                if parsed_date.year < 100:
                    if parsed_date.year < 50:
                        parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                    else:
                        parsed_date = parsed_date.replace(year=parsed_date.year + 1900)
                
                # Calcular confiança baseada em formato
                confidence = self._calculate_confidence(date_str, fmt)
                
                return parsed_date, confidence
                
            except ValueError:
                continue
        
        return None, 0.0
    
    def _calculate_confidence(self, date_str: str, format_used: str) -> float:
        """Calcula confiança baseada em características da data."""
        confidence = 0.8  # Base
        
        # Formato completo (YYYY) é mais confiável
        if 'Y' in format_used and len([c for c in format_used if c == 'Y']) == 4:
            confidence += 0.1
        
        # Separadores claros são mais confiáveis
        if '/' in date_str or '.' in date_str or '-' in date_str:
            confidence += 0.05
        
        # Normalizar para [0, 1]
        return min(confidence, 1.0)
    
    def _validate_date(self, date: datetime) -> bool:
        """Valida se a data está dentro dos critérios."""
        # Validar ano
        if date.year < self.min_year or date.year > self.max_year:
            logger.debug(f"❌ Ano fora do intervalo: {date.year} (min={self.min_year}, max={self.max_year})")
            return False
        
        # Validar se não é passado
        if not self.allow_past:
            now = datetime.now()
            if date < now:
                logger.debug(f"❌ Data no passado: {date.strftime('%d/%m/%Y')}")
                return False
        
        return True
    
    def format_date(self, date: datetime, format: str = '%d/%m/%Y') -> str:
        """Formata data para string."""
        return date.strftime(format)
    
    def __repr__(self) -> str:
        return f"DateParser(formats={len(self.date_formats)}, year_range=[{self.min_year}, {self.max_year}])"


class TextCleaner:
    """Limpeza e normalização de texto OCR."""
    
    @staticmethod
    def remove_special_chars(text: str, keep: str = '/.-') -> str:
        """Remove caracteres especiais, mantendo alguns."""
        pattern = f'[^a-zA-Z0-9{re.escape(keep)}\s]'
        cleaned = re.sub(pattern, '', text)
        return cleaned
    
    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normaliza espaços em branco."""
        return ' '.join(text.split())
    
    @staticmethod
    def remove_non_numeric(text: str, keep: str = '/.-') -> str:
        """Remove tudo exceto números e separadores."""
        pattern = f'[^0-9{re.escape(keep)}]'
        cleaned = re.sub(pattern, '', text)
        return cleaned
    
    @staticmethod
    def clean_for_date(text: str) -> str:
        """Limpeza específica para datas."""
        # Remover tudo exceto números e separadores
        cleaned = TextCleaner.remove_non_numeric(text, keep='/.-')
        # Normalizar espaços
        cleaned = TextCleaner.normalize_whitespace(cleaned)
        return cleaned.strip()


__all__ = ['DateParser', 'TextCleaner']
