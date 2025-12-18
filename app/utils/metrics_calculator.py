"""
Metrics calculation utilities
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculate Precision, Recall, and F1 score from feedback data"""
    
    @staticmethod
    def calculate_precision(true_positives: int, false_positives: int) -> Optional[float]:
        """
        Calculate Precision = TP / (TP + FP)
        
        Args:
            true_positives: Number of true positives
            false_positives: Number of false positives
            
        Returns:
            Precision score (0.0 to 1.0) or None if undefined
        """
        denominator = true_positives + false_positives
        if denominator == 0:
            return None
        return true_positives / denominator
    
    @staticmethod
    def calculate_recall(true_positives: int, false_negatives: int) -> Optional[float]:
        """
        Calculate Recall = TP / (TP + FN)
        
        Args:
            true_positives: Number of true positives
            false_negatives: Number of false negatives
            
        Returns:
            Recall score (0.0 to 1.0) or None if undefined
        """
        denominator = true_positives + false_negatives
        if denominator == 0:
            return None
        return true_positives / denominator
    
    @staticmethod
    def calculate_f1_score(precision: Optional[float], recall: Optional[float]) -> Optional[float]:
        """
        Calculate F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
        
        Args:
            precision: Precision score
            recall: Recall score
            
        Returns:
            F1 score (0.0 to 1.0) or None if undefined
        """
        if precision is None or recall is None:
            return None
        
        denominator = precision + recall
        if denominator == 0:
            return None
        
        return 2 * (precision * recall) / denominator
    
    @staticmethod
    def calculate_all_metrics(
        true_positives: int,
        false_positives: int,
        false_negatives: int,
        true_negatives: int = 0
    ) -> Dict[str, Optional[float]]:
        """
        Calculate all metrics at once.
        
        Args:
            true_positives: Number of true positives
            false_positives: Number of false positives
            false_negatives: Number of false negatives
            true_negatives: Number of true negatives (optional)
            
        Returns:
            Dictionary with precision, recall, f1_score
        """
        precision = MetricsCalculator.calculate_precision(true_positives, false_positives)
        recall = MetricsCalculator.calculate_recall(true_positives, false_negatives)
        f1_score = MetricsCalculator.calculate_f1_score(precision, recall)
        
        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "true_negatives": true_negatives
        }
    
    @staticmethod
    def aggregate_by_period(
        findings: List[Dict],
        period: str = "daily"
    ) -> List[Dict]:
        """
        Aggregate findings by time period.
        
        Args:
            findings: List of findings with feedback
            period: Aggregation period (daily, weekly, monthly)
            
        Returns:
            List of aggregated metrics by period
        """
        # TODO: Implement aggregation logic
        logger.info(f"Aggregating metrics by {period}")
        return []
    
    @staticmethod
    def aggregate_by_language(findings: List[Dict]) -> Dict[str, Dict]:
        """
        Aggregate metrics by programming language.
        
        Args:
            findings: List of findings with feedback
            
        Returns:
            Dictionary of metrics grouped by language
        """
        # TODO: Implement language aggregation
        logger.info("Aggregating metrics by language")
        return {}
    
    @staticmethod
    def aggregate_by_tool(findings: List[Dict]) -> Dict[str, Dict]:
        """
        Aggregate metrics by SAST tool.
        
        Args:
            findings: List of findings with feedback
            
        Returns:
            Dictionary of metrics grouped by tool
        """
        # TODO: Implement tool aggregation
        logger.info("Aggregating metrics by tool")
        return {}
    
    @staticmethod
    def aggregate_by_severity(findings: List[Dict]) -> Dict[str, Dict]:
        """
        Aggregate metrics by severity level.
        
        Args:
            findings: List of findings with feedback
            
        Returns:
            Dictionary of metrics grouped by severity
        """
        # TODO: Implement severity aggregation
        logger.info("Aggregating metrics by severity")
        return {}
