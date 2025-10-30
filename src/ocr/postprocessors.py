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
    """Parser completo que suporta TODOS os formatos de data comuns"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._build_month_mappings()
        self._build_patterns()
        
    def _build_month_mappings(self):
        """Mapeamento completo de meses"""
        self.MONTHS_DIRECT = {
            # Português
            'JAN': 1, 'FEV': 2, 'MAR': 3, 'ABR': 4, 'MAI': 5, 'JUN': 6,
            'JUL': 7, 'AGO': 8, 'SET': 9, 'OUT': 10, 'NOV': 11, 'DEZ': 12,
            # Inglês
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
    
    def _build_patterns(self):
        """TODOS os padrões de data possíveis"""
        self.patterns = [
            # DD/MM/YYYY ou DD/MM/YY (MAIS CONFIÁVEL)
            {
                'regex': re.compile(r'(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2,4})'),
                'type': 'numeric_slash',
                'confidence': 0.95
            },
            # DDMMMYY (01MAR26) - CONFIÁVEL
            {
                'regex': re.compile(r'(\d{1,2})?\s*([A-Z]{2,4})\s*(\d{2,4})', re.IGNORECASE),
                'type': 'abbreviated_month', 
                'confidence': 0.93
            },
            # YYYY-MM-DD
            {
                'regex': re.compile(r'(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})'),
                'type': 'numeric_inverse',
                'confidence': 0.90
            },
            # MMM/YYYY (MAR/2026)
            {
                'regex': re.compile(r'([A-Z]{3,4})[/.\-](\d{2,4})', re.IGNORECASE),
                'type': 'month_year',
                'confidence': 0.85
            },
            # DDMMYYYY (8 dígitos) - COMUM EM LOTES E VALIDADES
            {
                'regex': re.compile(r'(\d{2})(\d{2})(\d{4})'),
                'type': 'compact_8digits',
                'confidence': 0.88
            },
            # DDMMYY (6 dígitos) - COMUM EM LOTES
            {
                'regex': re.compile(r'(\d{2})(\d{2})(\d{2})'),
                'type': 'compact_6digits',
                'confidence': 0.75
            },
            # Padrão para textos como "LOT010720252 VAL27122025"
            {
                'regex': re.compile(r'(?:LOT|LOTE|VAL|VALIDADE|FAB)?(\d{2})(\d{2})(\d{4})'),
                'type': 'prefix_8digits',
                'confidence': 0.90
            },
            # Padrão para textos como "VAL27122025" 
            {
                'regex': re.compile(r'(VAL|VALIDADE)(\d{2})(\d{2})(\d{4})'),
                'type': 'val_prefix',
                'confidence': 0.92
            }
        ]

    def parse(self, text: str) -> Tuple[Optional[datetime], float]:
        """
        Extrai datas, ordena por confiança e escolhe a melhor
        
        Args:
            text: Texto OCR extraído
            
        Returns:
            Tuple (datetime, confidence) da data escolhida
        """
        if not text or not text.strip():
            return None, 0.0
            
        original_text = text.strip()
        logger.info(f"🎯 [COMPLETE PARSE] Texto: '{original_text}'")
        
        # Limpeza conservadora
        cleaned_text = self._conservative_cleanup(original_text)
        if cleaned_text != original_text:
            logger.info(f"🔧 Texto limpo: '{cleaned_text}'")
        
        # Extrai TODAS as datas
        all_dates = self._extract_all_dates(cleaned_text)
        
        if not all_dates:
            logger.warning(f"❌ Nenhuma data encontrada em: '{original_text}'")
            return None, 0.0
        
        # Ordena por CONFIANÇA (maior primeiro)
        all_dates.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"📊 Datas encontradas (ordenadas por confiança): {len(all_dates)}")
        for i, (date, conf) in enumerate(all_dates):
            marker = "🏆" if i == 0 else "🥈" if i == 1 else "   "
            logger.info(f"   {marker} {date.strftime('%d/%m/%Y')} (conf: {conf:.2f})")
        
        # Estratégia: pega as 2 melhores por confiança e escolhe a mais recente
        if len(all_dates) >= 2:
            best_date, best_conf = all_dates[0]
            second_date, second_conf = all_dates[1]
            
            # Se a segunda tem confiança similar (> 90% da melhor) e é mais recente, escolhe ela
            if second_conf >= best_conf * 0.9 and second_date > best_date:
                logger.info(f"🔀 Segunda opção mais recente com confiança similar")
                chosen_date, chosen_conf = second_date, second_conf
            else:
                chosen_date, chosen_conf = best_date, best_conf
                
        else:
            # Apenas uma data encontrada
            chosen_date, chosen_conf = all_dates[0]
        
        logger.success(f"✅ Data escolhida: {chosen_date.strftime('%d/%m/%Y')} (conf: {chosen_conf:.2f})")
        return chosen_date, chosen_conf
    
    def _conservative_cleanup(self, text: str) -> str:
        """Limpeza conservadora"""
        corrections = {
            'L0TE': 'LOTE', 'L0TE:': 'LOTE:',
            'VA1': 'VAL', 'VA1:': 'VAL:',
            'V4L': 'VAL', 'V4L:': 'VAL:',
            'F4B': 'FAB', 'F4B:': 'FAB:',
            ' :': ':', ' : ': ': ',
        }
        
        cleaned = text
        for wrong, right in corrections.items():
            cleaned = cleaned.replace(wrong, right)
        
        # Remove ruído pós-data
        cleaned = re.sub(r'(\d{1,2}[A-Z]{3}\d{2})[A-Z0-9]*\b', r'\1', cleaned)
        
        # Corrige anos
        cleaned = re.sub(r'\b25(\d{2})\b', r'20\1', cleaned)
        
        return cleaned.strip()
    
    def _extract_all_dates(self, text: str) -> List[Tuple[datetime, float]]:
        """Extrai TODAS as datas do texto"""
        all_dates = []
        text_upper = text.upper()
        
        for pattern_info in self.patterns:
            pattern = pattern_info['regex']
            base_confidence = pattern_info['confidence']
            
            for match in pattern.finditer(text_upper):
                try:
                    date_obj = self._parse_match(match, pattern_info['type'])
                    if date_obj and self._is_valid_date(date_obj):
                        # Ajusta confiança baseado no contexto
                        confidence = self._adjust_confidence(base_confidence, match.group(), text_upper, pattern_info['type'])
                        all_dates.append((date_obj, confidence))
                        logger.debug(f"  ✅ {pattern_info['type']}: {date_obj.strftime('%d/%m/%Y')} (conf: {confidence:.2f})")
                        
                except (ValueError, TypeError) as e:
                    logger.debug(f"  ⚠️  Erro no padrão {pattern_info['type']}: {e}")
                    continue
        
        return all_dates
    
    def _parse_match(self, match, pattern_type: str) -> Optional[datetime]:
        """Parse uma correspondência de regex"""
        groups = match.groups()
        
        if pattern_type == 'numeric_slash':
            day, month, year = map(int, groups)
            if year < 100:
                year += 2000
            return datetime(year, month, day)
        
        elif pattern_type == 'abbreviated_month':
            if len(groups) == 3:
                day_str, month_str, year_str = groups
                day = int(day_str) if day_str and day_str.isdigit() else 1
            else:
                return None
            
            month = self._parse_month(month_str.upper())
            if not month:
                return None
            
            year = int(year_str)
            if year < 100:
                year += 2000
                
            return datetime(year, month, day)
        
        elif pattern_type == 'numeric_inverse':
            year, month, day = map(int, groups)
            return datetime(year, month, day)
        
        elif pattern_type == 'month_year':
            month_str, year_str = groups
            month = self._parse_month(month_str.upper())
            if not month:
                return None
            
            year = int(year_str)
            if year < 100:
                year += 2000
                
            last_day = calendar.monthrange(year, month)[1]
            return datetime(year, month, last_day)
        
        elif pattern_type == 'compact_8digits':
            # DDMMYYYY (01072025 -> 01/07/2025)
            part1, part2, part3 = map(int, groups)
            
            # Tenta DD/MM/YYYY
            if 1 <= part1 <= 31 and 1 <= part2 <= 12:
                return datetime(part3, part2, part1)
            
            # Tenta MM/DD/YYYY  
            elif 1 <= part2 <= 31 and 1 <= part1 <= 12:
                return datetime(part3, part1, part2)
            
            return None
        
        elif pattern_type == 'compact_6digits':
            # DDMMYY (250630 -> 25/06/2030)
            part1, part2, part3 = map(int, groups)
            
            # Tenta DD/MM/YY
            if 1 <= part1 <= 31 and 1 <= part2 <= 12:
                return datetime(part3 + 2000, part2, part1)
            
            # Tenta MM/DD/YY  
            elif 1 <= part2 <= 31 and 1 <= part1 <= 12:
                return datetime(part3 + 2000, part1, part2)
            
            return None
        
        elif pattern_type == 'prefix_8digits':
            # LOT010720252 -> 01072025 (DDMMYYYY)
            # O primeiro grupo pode ser o prefixo, ignoramos
            if len(groups) == 3:
                part1, part2, part3 = map(int, groups)
            else:
                part1, part2, part3 = map(int, groups[1:4])
            
            # Tenta DD/MM/YYYY
            if 1 <= part1 <= 31 and 1 <= part2 <= 12:
                return datetime(part3, part2, part1)
            
            return None
        
        elif pattern_type == 'val_prefix':
            # VAL27122025 -> 27/12/2025
            prefix, part1, part2, part3 = groups
            part1, part2, part3 = map(int, [part1, part2, part3])
            
            # Tenta DD/MM/YYYY
            if 1 <= part1 <= 31 and 1 <= part2 <= 12:
                return datetime(part3, part2, part1)
            
            return None
        
        return None
    
    def _parse_month(self, month_str: str) -> Optional[int]:
        """Parse inteligente de mês"""
        month_str = month_str.upper().strip()
        
        # Mapeamento direto
        if month_str in self.MONTHS_DIRECT:
            return self.MONTHS_DIRECT[month_str]
        
        # Remove dígitos e tenta novamente
        letters_only = re.sub(r'\d', '', month_str)
        if letters_only in self.MONTHS_DIRECT:
            return self.MONTHS_DIRECT[letters_only]
        
        # Similaridade
        for known_month, month_num in self.MONTHS_DIRECT.items():
            if SequenceMatcher(None, month_str, known_month).ratio() > 0.6:
                return month_num
        
        return None
    
    def _adjust_confidence(self, base_confidence: float, date_text: str, full_text: str, pattern_type: str) -> float:
        """Ajusta confiança baseado em características específicas"""
        confidence = base_confidence
        
        # AUMENTA confiança se estiver perto de palavras-chave de validade
        if any(keyword in full_text for keyword in ['VAL', 'VALIDADE', 'EXP', 'VENC']):
            confidence += 0.05
        
        # REDUZ confiança se estiver perto de palavras-chave de lote (apenas para compactas)
        if any(keyword in full_text for keyword in ['LOTE', 'LOT', 'L']) and 'compact' in pattern_type:
            confidence *= 0.9
        
        # AUMENTA confiança para padrões com prefixo VAL (são quase sempre validade)
        if pattern_type == 'val_prefix':
            confidence += 0.08
        
        return min(confidence, 1.0)
    
    def _is_valid_date(self, date: datetime) -> bool:
        """Valida se a data é real"""
        try:
            datetime(date.year, date.month, date.day)
            return 2000 <= date.year <= 2040
        except ValueError:
            return False

__all__ = ["DateParser"]
