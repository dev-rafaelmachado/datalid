"""
📅 Pós-processadores de Texto OCR 
Parse e validação de datas extraídas com suporte a múltiplos formatos, idiomas e ruídos de OCR.
"""

import calendar
import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger


class DateParser:
    """Parser de datas extremamente robusto para textos OCR com ruído."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._build_month_mappings()
        self._build_patterns()
        
    def _build_month_mappings(self):
        """Mapeamento completo de meses em português e inglês"""
        self.MONTHS_PT = {
            'janeiro': 1, 'jan': 1, 'janr': 1, 'jane': 1,
            'fevereiro': 2, 'fev': 2, 'fevr': 2,
            'março': 3, 'marco': 3, 'mar': 3, 'mar¢o': 3, 'marco': 3,
            'abril': 4, 'abr': 4, 'abri': 4,
            'maio': 5, 'mai': 5, 'maio': 5,
            'junho': 6, 'jun': 6, 'junh': 6,
            'julho': 7, 'jul': 7, 'julh': 7,
            'agosto': 8, 'ago': 8, 'agos': 8,
            'setembro': 9, 'set': 9, 'sete': 9,
            'outubro': 10, 'out': 10, 'outu': 10,
            'novembro': 11, 'nov': 11, 'novo': 11,
            'dezembro': 12, 'dez': 12, 'deze': 12
        }
        
        self.MONTHS_EN = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        self.MONTHS_ABBR = {
            'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
        }
        
        self.all_months = {**self.MONTHS_PT, **self.MONTHS_EN, **self.MONTHS_ABBR}
    
    def _build_patterns(self):
        """Compila todos os padrões regex para detecção de datas"""
        # Padrão para datas do tipo 01MAR26 (seu caso específico)
        self.pattern_abr_month = re.compile(
            r'\b(\d{1,2})?\s*([A-Z]{3,4})\s*(\d{2,4})\b', 
            re.IGNORECASE
        )
        
        # Padrões numéricos com separadores
        self.patterns_numeric = [
            re.compile(r'\b(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})\b'),  # DD/MM/YYYY
            re.compile(r'\b(\d{2,4})[/.\-](\d{1,2})[/.\-](\d{1,2})\b'),  # YYYY/MM/DD
            re.compile(r'\b(\d{1,2})\s*[/.\-]\s*(\d{2,4})\b'),           # MM/YYYY
            re.compile(r'\b(\d{6,8})\b'),                                # DDMMYYYY ou MMDDYYYY
        ]
        
        # Padrões textuais
        self.patterns_text = [
            re.compile(r'\b(\d{1,2})?\s*(?:de\s+)?([a-z]+)\s*(?:de\s+)?(\d{2,4})\b', re.IGNORECASE),
            re.compile(r'\b([a-z]+)\s+(\d{1,2})\s*,?\s*(\d{2,4})\b', re.IGNORECASE),
            re.compile(r'\b([a-z]{3,})[/.\-\s]*(\d{2,4})\b', re.IGNORECASE),  # MAR/2026
        ]
        
        # Padrões agressivos para busca ampla
        self.patterns_aggressive = [
            re.compile(r'(\d{1,2})[^\w]?([A-Z]{3})[^\w]?(\d{2})'),  # 01-MAR-26
            re.compile(r'([A-Z]{3})[^\w]?(\d{1,2})[^\w]?(\d{2,4})'), # MAR-01-26
        ]
    
    def parse(self, text: str) -> Tuple[Optional[datetime], float]:
        """
        Parse robusto de data retornando a data e confiança
        
        Args:
            text: Texto OCR extraído
            
        Returns:
            Tuple (datetime, confidence) ou (None, 0.0) se não encontrado
        """
        if not text or not text.strip():
            return None, 0.0
            
        original_text = text.strip()
        logger.info(f"📅 [ULTRA PARSE] Texto: '{original_text}'")
        
        # Aplica correções OCR
        cleaned_text = self._apply_advanced_ocr_corrections(original_text)
        if cleaned_text != original_text:
            logger.info(f"🔧 Texto corrigido: '{cleaned_text}'")
        
        # Tenta múltiplas estratégias de parsing
        all_candidates = []
        
        # 1. Estratégia principal: datas com meses abreviados (01MAR26)
        all_candidates.extend(self._extract_abbreviated_month_dates(cleaned_text))
        
        # 2. Formatos numéricos tradicionais
        all_candidates.extend(self._extract_numeric_dates(cleaned_text))
        
        # 3. Formatos textuais
        all_candidates.extend(self._extract_textual_dates(cleaned_text))
        
        # 4. Busca agressiva
        all_candidates.extend(self._extract_aggressive_dates(cleaned_text))
        
        # 5. Fallback: procura por padrões próximos
        if not all_candidates:
            all_candidates.extend(self._extract_fallback_dates(cleaned_text))
        
        # Filtra e classifica candidatos
        valid_dates = self._filter_and_rank_dates(all_candidates)
        
        if not valid_dates:
            logger.warning(f"❌ Nenhuma data válida encontrada em: '{original_text}'")
            return None, 0.0
        
        # Retorna a melhor data
        best_date, best_confidence = valid_dates[0]
        logger.success(f"✅ Data extraída: {best_date.strftime('%d/%m/%Y')} (conf: {best_confidence:.2f})")
        return best_date, best_confidence
    
    def _apply_advanced_ocr_corrections(self, text: str) -> str:
        """Aplica correções avançadas para ruídos comuns de OCR"""
        corrections = {
            # Correções de caracteres
            'O': '0', 'o': '0', 'Q': '0', 'Ø': '0',
            'I': '1', 'l': '1', '|': '1', '!': '1',
            'Z': '2', 'z': '2',
            'A': '4', 
            'S': '5', 
            'G': '6', 
            'T': '7',
            'B': '8', 'R': '8',
            'g': '9', 'q': '9',
            
            # Correções contextuais para meses
            'M6': 'M', 'M8': 'M', 'MA': 'M',
            'AP': 'APR', 'AB': 'ABR',
            'lOTE': 'LOTE', 'L0TE': 'LOTE',
            'VA1': 'VAL', 'VAI': 'VAL',
        }
        
        # Aplica substituições diretas
        corrected = text
        for wrong, right in corrections.items():
            corrected = corrected.replace(wrong, right)
        
        # Padroniza separadores
        corrected = re.sub(r'[\s\.\-_]+', ' ', corrected)
        
        # Remove ruídos comuns após datas
        corrected = re.sub(r'(\d{1,2}[A-Z]{3}\d{2})[A-Z0-9]*\b', r'\1', corrected)
        corrected = re.sub(r'(\d{1,2}/\d{1,2}/\d{2,4})[^/\d\s]*\b', r'\1', corrected)
        
        # Corrige anos comuns
        corrected = re.sub(r'\b25(\d{2})\b', r'20\1', corrected)  # 2526 -> 2026
        corrected = re.sub(r'\b24(\d{2})\b', r'20\1', corrected)  # 2426 -> 2026
        
        return corrected.strip()
    
    def _extract_abbreviated_month_dates(self, text: str) -> List[Tuple[datetime, float]]:
        """Extrai datas no formato 01MAR26 (seu caso específico)"""
        candidates = []
        
        for match in self.pattern_abr_month.finditer(text):
            try:
                day_str, month_str, year_str = match.groups()
                
                # Parse do dia (opcional)
                day = int(day_str) if day_str else 1
                
                # Parse do mês
                month = self._parse_month_abbreviation(month_str.upper())
                if not month:
                    continue
                
                # Parse do ano
                year = int(year_str)
                if year < 100:
                    year += 2000  # 26 -> 2026
                
                # Valida e cria data
                if self._is_valid_date(year, month, day):
                    date_obj = datetime(year, month, day)
                    confidence = 0.95  # Alta confiança para este formato
                    candidates.append((date_obj, confidence))
                    logger.debug(f"  ✅ Formato abreviado: {day:02d}/{month:02d}/{year}")
                    
            except (ValueError, TypeError) as e:
                logger.debug(f"  ❌ Erro no formato abreviado: {e}")
                continue
                
        return candidates
    
    def _extract_numeric_dates(self, text: str) -> List[Tuple[datetime, float]]:
        """Extrai datas em formatos numéricos"""
        candidates = []
        
        for pattern in self.patterns_numeric:
            for match in pattern.finditer(text):
                try:
                    groups = match.groups()
                    
                    if len(groups) == 3:
                        # DD/MM/YYYY ou YYYY/MM/DD
                        if len(groups[2]) == 4:  # YYYY/MM/DD
                            year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                        else:  # DD/MM/YYYY
                            day, month, year = int(groups[0]), int(groups[1]), int(groups[2])
                            if year < 100:
                                year += 2000
                    
                    elif len(groups) == 2:
                        # MM/YYYY
                        month, year = int(groups[0]), int(groups[1])
                        if year < 100:
                            year += 2000
                        day = 1  # Primeiro dia do mês
                    
                    elif len(groups) == 1:
                        # DDMMYYYY
                        date_str = groups[0]
                        if len(date_str) == 6:
                            day, month, year = int(date_str[:2]), int(date_str[2:4]), int(date_str[4:]) + 2000
                        elif len(date_str) == 8:
                            day, month, year = int(date_str[:2]), int(date_str[2:4]), int(date_str[4:8])
                        else:
                            continue
                    
                    if self._is_valid_date(year, month, day):
                        date_obj = datetime(year, month, day)
                        confidence = 0.85
                        candidates.append((date_obj, confidence))
                        
                except (ValueError, TypeError):
                    continue
                    
        return candidates
    
    def _extract_textual_dates(self, text: str) -> List[Tuple[datetime, float]]:
        """Extrai datas com meses por extenso"""
        candidates = []
        text_lower = text.lower()
        
        for pattern in self.patterns_text:
            for match in pattern.finditer(text_lower):
                try:
                    groups = match.groups()
                    
                    if len(groups) == 3:
                        if groups[0].isdigit():
                            # "15 de março de 2025"
                            day, month_str, year_str = groups
                        else:
                            # "março 15 2025" 
                            month_str, day, year_str = groups
                    elif len(groups) == 2:
                        # "MAR/2026"
                        month_str, year_str = groups
                        day = 1
                    
                    # Parse do mês
                    month = self._parse_month_name(month_str)
                    if not month:
                        continue
                    
                    # Parse do ano
                    year = int(year_str)
                    if year < 100:
                        year += 2000
                    
                    # Parse do dia
                    day = int(day) if str(day).isdigit() else 1
                    
                    if self._is_valid_date(year, month, day):
                        date_obj = datetime(year, month, day)
                        confidence = 0.90
                        candidates.append((date_obj, confidence))
                        
                except (ValueError, TypeError):
                    continue
                    
        return candidates
    
    def _extract_aggressive_dates(self, text: str) -> List[Tuple[datetime, float]]:
        """Busca agressiva por padrões de data"""
        candidates = []
        
        for pattern in self.patterns_aggressive:
            for match in pattern.finditer(text.upper()):
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        # Tenta diferentes combinações
                        for day_idx, month_idx, year_idx in [(0, 1, 2), (1, 0, 2)]:
                            if groups[month_idx].isalpha() and groups[day_idx].isdigit():
                                month = self._parse_month_abbreviation(groups[month_idx])
                                if month:
                                    day = int(groups[day_idx])
                                    year = int(groups[year_idx])
                                    if year < 100:
                                        year += 2000
                                    
                                    if self._is_valid_date(year, month, day):
                                        date_obj = datetime(year, month, day)
                                        candidates.append((date_obj, 0.75))
                                        break
                except (ValueError, TypeError):
                    continue
                    
        return candidates
    
    def _extract_fallback_dates(self, text: str) -> List[Tuple[datetime, float]]:
        """Fallback: procura por qualquer padrão que se pareça com data"""
        candidates = []
        
        # Procura por padrão DDMMMYY em qualquer lugar do texto
        fallback_pattern = re.compile(r'(\d{1,2})([A-Z]{3,4})(\d{2})', re.IGNORECASE)
        
        for match in fallback_pattern.finditer(text):
            try:
                day_str, month_str, year_str = match.groups()
                day = int(day_str)
                month = self._parse_month_abbreviation(month_str.upper())
                year = int(year_str) + 2000
                
                if month and self._is_valid_date(year, month, day):
                    date_obj = datetime(year, month, day)
                    candidates.append((date_obj, 0.65))  # Confiança mais baixa
                    
            except (ValueError, TypeError):
                continue
                
        return candidates
    
    def _parse_month_abbreviation(self, month_str: str) -> Optional[int]:
        """Parse robusto de abreviações de mês"""
        if not month_str:
            return None
            
        month_str = month_str.upper().strip()
        
        # Mapeamento direto
        direct_map = {
            'JAN': 1, 'FEB': 2, 'FEV': 2, 'MAR': 3, 'APR': 4, 'ABR': 4,
            'MAY': 5, 'MAI': 5, 'JUN': 6, 'JUL': 7, 'AUG': 8, 'AGO': 8,
            'SEP': 9, 'SET': 9, 'OCT': 10, 'OUT': 10, 'NOV': 11, 'DEC': 12, 'DEZ': 12
        }
        
        if month_str in direct_map:
            return direct_map[month_str]
        
        # Tenta correções comuns de OCR
        corrections = {
            'MARC': 'MAR', 'MARS': 'MAR', 'MARÇ': 'MAR',
            'APRI': 'APR', 'ABRI': 'ABR',
            'JUNE': 'JUN', 'JULY': 'JUL',
            'AUGU': 'AUG', 'SEPT': 'SEP',
            'OCTO': 'OCT', 'DECE': 'DEC'
        }
        
        if month_str in corrections:
            return direct_map.get(corrections[month_str])
        
        # Busca por similaridade
        for known_month, month_num in direct_map.items():
            if SequenceMatcher(None, month_str, known_month).ratio() > 0.7:
                return month_num
                
        return None
    
    def _parse_month_name(self, month_str: str) -> Optional[int]:
        """Parse de nomes completos de mês com tolerância a erros"""
        if not month_str:
            return None
            
        month_lower = month_str.lower().strip()
        
        # Busca direta
        if month_lower in self.all_months:
            return self.all_months[month_lower]
        
        # Busca por similaridade
        for month_name, month_num in self.all_months.items():
            if SequenceMatcher(None, month_lower, month_name).ratio() > 0.7:
                return month_num
                
        return None
    
    def _is_valid_date(self, year: int, month: int, day: int) -> bool:
        """Valida se é uma data real"""
        try:
            datetime(year, month, day)
            
            # Validação de intervalo razoável
            if year < 2000 or year > 2040:
                return False
            if month < 1 or month > 12:
                return False
            if day < 1 or day > 31:
                return False
                
            return True
        except ValueError:
            return False
    
    def _filter_and_rank_dates(self, candidates: List[Tuple[datetime, float]]) -> List[Tuple[datetime, float]]:
        """Filtra e classifica as datas encontradas"""
        if not candidates:
            return []
        
        # Remove duplicatas
        unique_dates = {}
        for date, confidence in candidates:
            date_key = date.strftime('%Y-%m-%d')
            if date_key not in unique_dates or confidence > unique_dates[date_key][1]:
                unique_dates[date_key] = (date, confidence)
        
        # Ordena por confiança (mais alta primeiro)
        sorted_dates = sorted(unique_dates.values(), key=lambda x: x[1], reverse=True)
        
        return sorted_dates

__all__ = ["DateParser"]
