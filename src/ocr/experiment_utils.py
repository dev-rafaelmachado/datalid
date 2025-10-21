"""
🧪 Experiment Utilities
Utilitários para experimentação, ablation tests e avaliação de OCR.

Facilita comparação de diferentes configurações e estratégias.
"""

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from loguru import logger

# Import condicional para Levenshtein
try:
    from Levenshtein import distance as levenshtein_distance
    HAS_LEVENSHTEIN = True
except ImportError:
    HAS_LEVENSHTEIN = False


@dataclass
class OCRResult:
    """Resultado de OCR com metadados."""
    text: str
    confidence: float
    processing_time: float
    variant_used: Optional[str] = None
    num_lines: int = 1
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ExperimentMetrics:
    """Métricas de experimento."""
    cer: float  # Character Error Rate
    wer: float  # Word Error Rate
    exact_match_rate: float  # Taxa de match exato
    avg_confidence: float
    avg_processing_time: float
    line_ordering_errors: int = 0
    num_samples: int = 0
    
    def to_dict(self) -> dict:
        """Converte para dicionário."""
        return asdict(self)


class ExperimentRunner:
    """
    Runner para experimentos de OCR.
    
    Facilita testes de ablação e comparação de configurações.
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Inicializa runner.
        
        Args:
            output_dir: Diretório para salvar resultados
        """
        self.output_dir = Path(output_dir) if output_dir else Path("outputs/experiments")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
    
    def run_ablation_test(
        self,
        ocr_engine,
        test_images: List[np.ndarray],
        ground_truths: List[str],
        configurations: Dict[str, dict]
    ) -> Dict[str, ExperimentMetrics]:
        """
        Executa teste de ablação com diferentes configurações.
        
        Args:
            ocr_engine: Instância do engine OCR
            test_images: Lista de imagens de teste
            ground_truths: Lista de textos esperados
            configurations: Dict {nome: config} de configurações a testar
            
        Returns:
            Dict {nome_config: métricas}
        """
        results = {}
        
        for config_name, config in configurations.items():
            logger.info(f"🧪 Testando configuração: {config_name}")
            
            # Aplicar configuração
            self._apply_config(ocr_engine, config)
            
            # Executar OCR
            predictions = []
            confidences = []
            times = []
            
            for img, gt in zip(test_images, ground_truths):
                start = time.time()
                text, conf = ocr_engine.extract_text(img)
                elapsed = time.time() - start
                
                predictions.append(text)
                confidences.append(conf)
                times.append(elapsed)
            
            # Calcular métricas
            metrics = self.calculate_metrics(predictions, ground_truths, confidences, times)
            results[config_name] = metrics
            
            logger.info(f"   CER: {metrics.cer:.4f}, Exact Match: {metrics.exact_match_rate:.2%}")
        
        # Salvar resultados
        self._save_results(results, "ablation_test")
        
        return results
    
    def calculate_metrics(
        self,
        predictions: List[str],
        ground_truths: List[str],
        confidences: List[float],
        times: List[float]
    ) -> ExperimentMetrics:
        """
        Calcula métricas de avaliação.
        
        Args:
            predictions: Textos preditos
            ground_truths: Textos esperados
            confidences: Confianças
            times: Tempos de processamento
            
        Returns:
            Métricas calculadas
        """
        # CER (Character Error Rate)
        total_cer = 0.0
        for pred, gt in zip(predictions, ground_truths):
            cer = self._calculate_cer(pred, gt)
            total_cer += cer
        avg_cer = total_cer / len(predictions) if predictions else 1.0
        
        # WER (Word Error Rate)
        total_wer = 0.0
        for pred, gt in zip(predictions, ground_truths):
            wer = self._calculate_wer(pred, gt)
            total_wer += wer
        avg_wer = total_wer / len(predictions) if predictions else 1.0
        
        # Exact Match Rate
        exact_matches = sum(1 for pred, gt in zip(predictions, ground_truths) 
                           if pred.strip() == gt.strip())
        exact_match_rate = exact_matches / len(predictions) if predictions else 0.0
        
        # Médias
        avg_confidence = np.mean(confidences) if confidences else 0.0
        avg_time = np.mean(times) if times else 0.0
        
        return ExperimentMetrics(
            cer=avg_cer,
            wer=avg_wer,
            exact_match_rate=exact_match_rate,
            avg_confidence=avg_confidence,
            avg_processing_time=avg_time,
            num_samples=len(predictions)
        )
    
    def _calculate_cer(self, prediction: str, ground_truth: str) -> float:
        """
        Calcula Character Error Rate.
        
        CER = edit_distance(pred, gt) / len(gt)
        """
        if not ground_truth:
            return 1.0 if prediction else 0.0
        
        if HAS_LEVENSHTEIN:
            distance = levenshtein_distance(prediction, ground_truth)
        else:
            # Fallback: implementação simples de edit distance
            distance = self._simple_edit_distance(prediction, ground_truth)
        
        return distance / len(ground_truth)
    
    def _calculate_wer(self, prediction: str, ground_truth: str) -> float:
        """
        Calcula Word Error Rate.
        
        WER = edit_distance(words_pred, words_gt) / len(words_gt)
        """
        pred_words = prediction.split()
        gt_words = ground_truth.split()
        
        if not gt_words:
            return 1.0 if pred_words else 0.0
        
        if HAS_LEVENSHTEIN:
            distance = levenshtein_distance(pred_words, gt_words)
        else:
            distance = self._simple_edit_distance(pred_words, gt_words)
        
        return distance / len(gt_words)
    
    def _simple_edit_distance(self, s1: str, s2: str) -> int:
        """
        Implementação simples de edit distance (Levenshtein).
        
        Fallback quando python-Levenshtein não está disponível.
        """
        len1, len2 = len(s1), len(s2)
        
        # Matriz de distâncias
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Inicializar primeira linha e coluna
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j
        
        # Preencher matriz
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],    # Deleção
                        dp[i][j-1],    # Inserção
                        dp[i-1][j-1]   # Substituição
                    )
        
        return dp[len1][len2]
    
    def _apply_config(self, ocr_engine, config: dict) -> None:
        """Aplica configuração ao engine."""
        # Atualizar atributos do engine
        for key, value in config.items():
            if hasattr(ocr_engine, key):
                setattr(ocr_engine, key, value)
    
    def _save_results(self, results: Dict[str, ExperimentMetrics], experiment_name: str) -> None:
        """Salva resultados em JSON."""
        output_file = self.output_dir / f"{experiment_name}_{int(time.time())}.json"
        
        # Converter métricas para dict
        results_dict = {
            name: metrics.to_dict() 
            for name, metrics in results.items()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Resultados salvos em: {output_file}")


class ConfigurationPresets:
    """
    Presets de configurações para experimentos.
    
    Facilita criação de ablation tests.
    """
    
    @staticmethod
    def get_baseline() -> dict:
        """Configuração baseline (mínima)."""
        return {
            'enable_line_detection': False,
            'enable_geometric_norm': False,
            'enable_photometric_norm': False,
            'enable_ensemble': False
        }
    
    @staticmethod
    def get_line_detection_only() -> dict:
        """Apenas detecção de linhas."""
        baseline = ConfigurationPresets.get_baseline()
        baseline['enable_line_detection'] = True
        return baseline
    
    @staticmethod
    def get_geometric_norm_only() -> dict:
        """Apenas normalização geométrica."""
        baseline = ConfigurationPresets.get_baseline()
        baseline['enable_geometric_norm'] = True
        return baseline
    
    @staticmethod
    def get_photometric_norm_only() -> dict:
        """Apenas normalização fotométrica."""
        baseline = ConfigurationPresets.get_baseline()
        baseline['enable_photometric_norm'] = True
        return baseline
    
    @staticmethod
    def get_ensemble_only() -> dict:
        """Apenas ensemble de variantes."""
        baseline = ConfigurationPresets.get_baseline()
        baseline['enable_ensemble'] = True
        baseline['enable_photometric_norm'] = True  # Necessário para variantes
        return baseline
    
    @staticmethod
    def get_full_pipeline() -> dict:
        """Pipeline completo."""
        return {
            'enable_line_detection': True,
            'enable_geometric_norm': True,
            'enable_photometric_norm': True,
            'enable_ensemble': True,
            'ensemble_strategy': 'rerank'
        }
    
    @staticmethod
    def get_ablation_configs() -> Dict[str, dict]:
        """Retorna conjunto completo de configurações para ablation test."""
        return {
            '1_baseline': ConfigurationPresets.get_baseline(),
            '2_line_detection': ConfigurationPresets.get_line_detection_only(),
            '3_geometric_norm': ConfigurationPresets.get_geometric_norm_only(),
            '4_photometric_norm': ConfigurationPresets.get_photometric_norm_only(),
            '5_ensemble': ConfigurationPresets.get_ensemble_only(),
            '6_full_pipeline': ConfigurationPresets.get_full_pipeline(),
        }


# Exemplo de parâmetros recomendados
RECOMMENDED_PARAMS = {
    'geometric_normalizer': {
        'enable_deskew': True,
        'max_angle': 10,
        'enable_perspective': False,  # Geralmente muito agressivo
        'target_heights': [32, 64, 128],
        'maintain_aspect': True
    },
    'photometric_normalizer': {
        'denoise_method': 'bilateral',  # Melhor que median para texto
        'shadow_removal': True,
        'clahe_enabled': True,
        'clahe_clip_limit': 1.5,  # 1.2-1.6 recomendado
        'clahe_tile_grid': [8, 8],  # 4x4 ou 8x8
        'sharpen_enabled': True,
        'sharpen_strength': 0.3
    },
    'line_detector': {
        'method': 'hybrid',
        'min_line_height': 10,
        'max_line_gap': 5,
        'dbscan_eps': 15,
        'enable_rotation_detection': True,
        'max_rotation_angle': 5.0,
        'clustering_method': 'dbscan'  # ou 'agglomerative'
    },
    'postprocessor': {
        'uppercase': True,
        'remove_symbols': False,
        'ambiguity_mapping': True,
        'fix_formats': True,
        'enable_fuzzy_match': True,
        'fuzzy_threshold': 2
    }
}


__all__ = [
    'OCRResult',
    'ExperimentMetrics',
    'ExperimentRunner',
    'ConfigurationPresets',
    'RECOMMENDED_PARAMS'
]
