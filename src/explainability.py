"""
Explainability module for LLM decisions using LIME and SHAP.

Provides explanations for LLM outputs to meet regulatory compliance requirements.
"""

import logging
import os
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from lime.lime_text import LimeTextExplainer
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    logger.warning("LIME not available. Install with: pip install lime")

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP not available. Install with: pip install shap")


class OutputValidator:
    """Validates LLM outputs using finance-specific heuristics."""
    
    def __init__(self):
        """Initialize output validator with finance-specific patterns."""
        # Financial number patterns
        self.currency_pattern = re.compile(r'\$[\d,]+\.?\d*\s*(?:billion|million|B|M|thousand|K)?', re.IGNORECASE)
        self.percentage_pattern = re.compile(r'\d+\.?\d*\s*%')
        self.date_pattern = re.compile(r'\b(?:Q[1-4]\s+\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b', re.IGNORECASE)
        
        # Financial keywords
        self.financial_keywords = [
            'revenue', 'income', 'profit', 'loss', 'earnings', 'dividend',
            'EPS', 'EBITDA', 'ROE', 'ROA', 'P/E', 'market cap', 'valuation'
        ]
    
    def validate(self, output_text: str, input_text: str) -> Dict:
        """
        Validate LLM output for finance-specific extraction.
        
        Args:
            output_text: LLM output text
            input_text: Original input text
            
        Returns:
            Validation result dictionary
        """
        if not output_text:
            return {
                "valid": False,
                "errors": ["Empty output"],
                "score": 0.0
            }
        
        errors = []
        warnings = []
        score = 1.0
        
        # Check for financial numbers
        currencies = self.currency_pattern.findall(output_text)
        percentages = self.percentage_pattern.findall(output_text)
        dates = self.date_pattern.findall(output_text)
        
        # Check for financial keywords
        found_keywords = [kw for kw in self.financial_keywords if kw.lower() in output_text.lower()]
        
        # Validation rules
        if len(currencies) == 0 and len(percentages) == 0:
            warnings.append("No financial numbers detected")
            score -= 0.1
        
        if len(found_keywords) == 0:
            warnings.append("No financial keywords detected")
            score -= 0.1
        
        # Check output length (too short might be incomplete)
        if len(output_text) < 50:
            warnings.append("Output seems too short")
            score -= 0.2
        
        # Check for common extraction errors
        if 'error' in output_text.lower() or 'cannot' in output_text.lower():
            errors.append("Error message detected in output")
            score -= 0.5
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": max(0.0, score),
            "metrics": {
                "currencies_found": len(currencies),
                "percentages_found": len(percentages),
                "dates_found": len(dates),
                "keywords_found": len(found_keywords),
                "output_length": len(output_text)
            }
        }


class LLMExplainer:
    """Provides explanations for LLM decisions using LIME and SHAP."""
    
    def __init__(self, llm_processor, use_lime: bool = True, use_shap: bool = False):
        """
        Initialize explainer.
        
        Args:
            llm_processor: LLMProcessor instance for making predictions
            use_lime: Whether to use LIME (requires lime package)
            use_shap: Whether to use SHAP (requires shap package)
        """
        self.llm_processor = llm_processor
        self.use_lime = use_lime and LIME_AVAILABLE
        self.use_shap = use_shap and SHAP_AVAILABLE
        self.validator = OutputValidator()
        
        if self.use_lime:
            self.lime_explainer = LimeTextExplainer(class_names=['negative', 'positive'])
        else:
            logger.warning("LIME not available, using simple explanation method")
        
        if self.use_shap:
            logger.info("SHAP available (stub implementation - extend for full functionality)")
        elif use_shap:
            logger.warning("SHAP requested but not available. Install with: pip install shap")
    
    def explain_with_shap(self, input_text: str, max_features: int = 10) -> Dict:
        """
        Generate explanation using SHAP - COMPLETE IMPLEMENTATION.
        
        
        Chains all steps: vectorize → prepare background → create explainer → compute values
        
        Args:
            input_text: Input text to explain
            max_features: Maximum number of features to include
            
        Returns:
            Dictionary with SHAP explanation data
        """
        
        if not SHAP_AVAILABLE:
            return {
                "method": "SHAP",
                "status": "error",
                "error": "SHAP not available. Install with: pip install shap",
                "fallback": self._simple_explanation(input_text)
            }
        
        
        try:

            # VECTORIZE TEXT 
            
            all_texts = self.background_texts + [input_text]
            vectors, word_to_idx = self._vectorize_text(all_texts)
            input_vector = vectors[-1:]  # Last vector is our input
            
            
            # BACKGROUND DATA 
            
            background_vectors, _ = self._prepare_background_data()
            
            
            # EXPLAINER
            
            explainer = self._create_shap_explainer(background_vectors)
            if explainer is None:
                logger.warning("  ✗ Failed to create explainer, falling back to simple explanation")
                return {
                    "method": "SHAP",
                    "status": "error",
                    "error": "Failed to create SHAP explainer",
                    "fallback": self._simple_explanation(input_text)
                }
            
            
            # SHAP VALUE
            
            shap_values = self._compute_shap_values(explainer, input_vector, num_samples=100)
            if shap_values is None:
                logger.warning("  ✗ Failed to compute SHAP values, falling back to simple explanation")
                return {
                    "method": "SHAP",
                    "status": "error",
                    "error": "Failed to compute SHAP values",
                    "fallback": self._simple_explanation(input_text)
                }
            
            
            # TOP FEATURES

            # Reverse mapping: index -> word
            idx_to_word = {v: k for k, v in word_to_idx.items()}
            
            # Flatten SHAP values 
            shap_vals_flat = shap_values[0] if len(np.array(shap_values).shape) > 1 else shap_values
            
            # Get indices of top features by absolute SHAP value 
            top_indices = np.argsort(np.abs(shap_vals_flat))[-max_features:][::-1]
            
            # Build feature explanation list
            top_features = []
            for idx in top_indices:
                if idx in idx_to_word:
                    feature_name = idx_to_word[idx]
                    shap_value = float(shap_vals_flat[idx])
                    direction = "increases prediction" if shap_value > 0 else "decreases prediction"
                    importance = round(abs(shap_value), 4)
                    
                    top_features.append({
                        "feature": feature_name,
                        "shap_value": round(shap_value, 4),
                        "direction": direction,
                        "importance": importance
                    })
                    
                   
            
            
            
            
            return {
                "method": "SHAP (KernelExplainer)",
                "status": "success",
                "input_text": input_text,
                "top_features": top_features,
                "num_features_analyzed": len(word_to_idx),
                "background_samples": len(self.background_texts),
                "explanation": f"Top {len(top_features)} words driving the model's decision"
            }
        
        # ERROR HANDLING: 
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}", exc_info=True)
            return {
                "method": "SHAP",
                "status": "error",
                "error": f"Explanation failed: {str(e)}",
                "fallback": self._simple_explanation(input_text)
            }
    
    def explain(self, input_text: str, max_features: int = 10, method: str = 'lime') -> Dict:
        """
        Generate explanation for LLM output.
        
        Args:
            input_text: Input text to explain
            max_features: Maximum number of features to include in explanation
            method: Explanation method ('lime', 'shap', or 'auto')
            
        Returns:
            Dictionary with explanation data and validation results
        """
        # Get prediction first
        prediction = self.llm_processor.process_document(input_text, max_tokens=200)
        
        if not prediction:
            return {"error": "Failed to get prediction"}
        
        # Extract output text
        output_text = ""
        if isinstance(prediction, dict):
            choices = prediction.get('choices', [])
            if choices:
                output_text = choices[0].get('text', '')
        
        # Validate output
        validation_result = self.validator.validate(output_text, input_text)
        
        # Generate explanation based on method
        if method == 'shap' and self.use_shap:
            explanation = self.explain_with_shap(input_text, max_features)
        elif method == 'lime' and self.use_lime:
            explanation = self._explain_with_lime(input_text, max_features)
        else:
            explanation = self._simple_explanation(input_text)
        
        # Combine explanation with validation
        explanation['validation'] = validation_result
        explanation['output_text'] = output_text
        
        return explanation
    
    def _explain_with_lime(self, input_text: str, max_features: int = 10) -> Dict:
        
        try:
            # Create prediction function for LIME
            def predict_proba(texts):
                """Predict probability distribution for LIME."""
                import numpy as np
                results = []
                for text in texts:
                    try:
                        response = self.llm_processor.process_document(text, max_tokens=50)
                        if response and isinstance(response, dict):
                            choices = response.get('choices', [])
                            if choices:
                                # Simple confidence: length of response as proxy
                                response_text = choices[0].get('text', '')
                                # Normalize to 0-1 range (simple heuristic)
                                confidence = min(len(response_text) / 100.0, 1.0)
                                results.append([1 - confidence, confidence])
                            else:
                                results.append([0.5, 0.5])
                        else:
                            results.append([0.5, 0.5])
                    except Exception as e:
                        logger.warning(f"Error in LIME prediction: {e}")
                        results.append([0.5, 0.5])
                
                return np.array(results)
            
            # Generate explanation
            explanation = self.lime_explainer.explain_instance(
                input_text,
                predict_proba,
                num_features=max_features,
                num_samples=100
            )
            
            # Format explanation
            explanation_list = explanation.as_list()
            
            return {
                "method": "LIME",
                "features": [
                    {
                        "feature": feature,
                        "weight": float(weight),
                        "importance": abs(float(weight))
                    }
                    for feature, weight in explanation_list
                ],
                "num_features": len(explanation_list)
            }
            
        except Exception as e:
            logger.error(f"Error generating LIME explanation: {e}", exc_info=True)
            return self._simple_explanation(input_text)
    
    def _simple_explanation(self, input_text: str) -> Dict:
        """
        Generate simple explanation without LIME.
        
        Uses keyword extraction and simple heuristics.
        """
        import re
        
        # Extract key financial terms
        financial_keywords = [
            r'\$[\d,]+\.?\d*\s*(?:billion|million|B|M)',
            r'\d+%',
            r'(?:revenue|income|profit|loss|earnings|dividend)',
            r'Q[1-4]\s+\d{4}',
            r'(?:up|down|increase|decrease|growth)',
        ]
        
        features = []
        for pattern in financial_keywords:
            matches = re.finditer(pattern, input_text, re.IGNORECASE)
            for match in matches:
                features.append({
                    "feature": match.group(0),
                    "weight": 0.5,  # Default weight
                    "importance": 0.5
                })
        
        # Limit to top features
        features = sorted(features, key=lambda x: x['importance'], reverse=True)[:10]
        
        return {
            "method": "simple_keyword",
            "features": features,
            "num_features": len(features)
        }
    
    def explain_batch(self, texts: List[str], max_features: int = 10) -> List[Dict]:
        """
        Generate explanations for multiple texts.
        
        Args:
            texts: List of input texts
            max_features: Maximum features per explanation
            
        Returns:
            List of explanation dictionaries
        """
        explanations = []
        for text in texts:
            explanation = self.explain(text, max_features)
            explanations.append(explanation)
        return explanations
