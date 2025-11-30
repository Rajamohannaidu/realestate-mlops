# src/explainability.py

import numpy as np
import pandas as pd
import shap
from lime import lime_tabular
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class ModelExplainability:
    """Provide model interpretability using SHAP and LIME"""
    
    def __init__(self, model, X_train, feature_names):
        self.model = model
        self.X_train = X_train
        self.feature_names = feature_names
        self.shap_explainer = None
        self.lime_explainer = None
        
    def initialize_shap(self):
        """Initialize SHAP explainer"""
        try:
            # Try TreeExplainer for tree-based models
            self.shap_explainer = shap.TreeExplainer(self.model)
            print("Using SHAP TreeExplainer")
        except:
            try:
                # Fallback to KernelExplainer
                background = shap.sample(self.X_train, 100)
                self.shap_explainer = shap.KernelExplainer(
                    self.model.predict, background
                )
                print("Using SHAP KernelExplainer")
            except Exception as e:
                print(f"Could not initialize SHAP: {e}")
                
    def initialize_lime(self):
        """Initialize LIME explainer"""
        try:
            self.lime_explainer = lime_tabular.LimeTabularExplainer(
                self.X_train.values if isinstance(self.X_train, pd.DataFrame) else self.X_train,
                feature_names=self.feature_names,
                mode='regression',
                random_state=42
            )
            print("LIME explainer initialized")
        except Exception as e:
            print(f"Could not initialize LIME: {e}")
    
    def get_shap_values(self, X):
        """Calculate SHAP values for given instances"""
        if self.shap_explainer is None:
            self.initialize_shap()
        
        if self.shap_explainer is None:
            return None
        
        try:
            shap_values = self.shap_explainer.shap_values(X)
            return shap_values
        except Exception as e:
            print(f"Error calculating SHAP values: {e}")
            return None
    
    def explain_prediction_shap(self, instance, instance_index=0):
        """
        Explain a single prediction using SHAP
        Returns feature importance for the prediction
        """
        shap_values = self.get_shap_values(instance)
        
        if shap_values is None:
            return None
        
        if len(shap_values.shape) > 1:
            shap_values_instance = shap_values[instance_index]
        else:
            shap_values_instance = shap_values
        
        # Create explanation dictionary
        explanation = {}
        for i, feature in enumerate(self.feature_names):
            explanation[feature] = {
                'shap_value': float(shap_values_instance[i]),
                'feature_value': float(instance.iloc[instance_index, i] if isinstance(instance, pd.DataFrame) 
                                      else instance[instance_index, i])
            }
        
        # Sort by absolute SHAP value
        sorted_explanation = dict(
            sorted(explanation.items(), 
                   key=lambda x: abs(x[1]['shap_value']), 
                   reverse=True)
        )
        
        return sorted_explanation
    
    def explain_prediction_lime(self, instance, num_features=10):
        """
        Explain a single prediction using LIME
        """
        if self.lime_explainer is None:
            self.initialize_lime()
        
        if self.lime_explainer is None:
            return None
        
        try:
            instance_array = instance.values[0] if isinstance(instance, pd.DataFrame) else instance[0]
            
            explanation = self.lime_explainer.explain_instance(
                instance_array,
                self.model.predict,
                num_features=num_features
            )
            
            # Extract feature contributions
            lime_explanation = {}
            for feature, weight in explanation.as_list():
                lime_explanation[feature] = weight
            
            return lime_explanation
        except Exception as e:
            print(f"Error with LIME explanation: {e}")
            return None
    
    def get_global_feature_importance(self, X_sample=None, max_samples=100):
        """
        Get global feature importance using SHAP
        """
        if X_sample is None:
            # Sample from training data
            if len(self.X_train) > max_samples:
                indices = np.random.choice(len(self.X_train), max_samples, replace=False)
                X_sample = self.X_train.iloc[indices] if isinstance(self.X_train, pd.DataFrame) else self.X_train[indices]
            else:
                X_sample = self.X_train
        
        shap_values = self.get_shap_values(X_sample)
        
        if shap_values is None:
            return None
        
        # Calculate mean absolute SHAP values
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        # Create importance dictionary
        importance = {}
        for i, feature in enumerate(self.feature_names):
            importance[feature] = float(mean_abs_shap[i])
        
        # Sort by importance
        sorted_importance = dict(
            sorted(importance.items(), key=lambda x: x[1], reverse=True)
        )
        
        return sorted_importance
    
    def generate_explanation_text(self, explanation, prediction_value):
        """
        Generate human-readable explanation text
        """
        text_lines = [
            f"Predicted Property Price: ${prediction_value:,.2f}\n",
            "Top factors influencing this prediction:\n"
        ]
        
        # Get top 5 features
        top_features = list(explanation.items())[:5]
        
        for i, (feature, data) in enumerate(top_features, 1):
            if 'shap_value' in data:
                impact = data['shap_value']
                value = data['feature_value']
            else:
                impact = data
                value = "N/A"
            
            impact_direction = "increases" if impact > 0 else "decreases"
            text_lines.append(
                f"{i}. {feature} (value: {value:.2f}): {impact_direction} "
                f"price by ${abs(impact):,.2f}"
            )
        
        return "\n".join(text_lines)
    
    def compare_explanations(self, instance):
        """
        Compare SHAP and LIME explanations for the same instance
        """
        prediction = self.model.predict(instance)[0]
        
        # Get SHAP explanation
        shap_exp = self.explain_prediction_shap(instance)
        shap_text = self.generate_explanation_text(shap_exp, prediction) if shap_exp else "SHAP unavailable"
        
        # Get LIME explanation
        lime_exp = self.explain_prediction_lime(instance)
        lime_text = self.generate_explanation_text(lime_exp, prediction) if lime_exp else "LIME unavailable"
        
        return {
            'prediction': prediction,
            'shap_explanation': shap_exp,
            'shap_text': shap_text,
            'lime_explanation': lime_exp,
            'lime_text': lime_text
        }
    
    def save_shap_summary_plot(self, X_sample, filepath='shap_summary.png'):
        """
        Generate and save SHAP summary plot
        """
        shap_values = self.get_shap_values(X_sample)
        
        if shap_values is None:
            print("Cannot generate SHAP plot")
            return
        
        plt.figure(figsize=(10, 6))
        shap.summary_plot(
            shap_values, 
            X_sample, 
            feature_names=self.feature_names,
            show=False
        )
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"SHAP summary plot saved to {filepath}")

# Example usage
if __name__ == "__main__":
    from data_preprocessing import RealEstateDataPreprocessor
    from predictive_models import RealEstatePredictiveModels
    
    # Load data
    preprocessor = RealEstateDataPreprocessor()
    df = preprocessor.load_data('data/sample_data.csv')
    df = preprocessor.clean_data(df)
    df = preprocessor.feature_engineering(df)
    
    categorical_cols = ['location', 'property_type']
    df_encoded = preprocessor.encode_categorical(df, categorical_cols)
    
    X_train, X_test, y_train, y_test = preprocessor.prepare_features(df_encoded)
    
    # Train a model
    models = RealEstatePredictiveModels()
    models.models['random_forest'] = RandomForestRegressor(n_estimators=100, random_state=42)
    models.models['random_forest'].fit(X_train, y_train)
    
    # Initialize explainability
    explainer = ModelExplainability(
        models.models['random_forest'],
        X_train,
        preprocessor.feature_names
    )
    
    # Explain a single prediction
    test_instance = X_test.iloc[[0]]
    comparison = explainer.compare_explanations(test_instance)
    
    print("=== PREDICTION EXPLANATION ===\n")
    print(comparison['shap_text'])
    print("\n" + "="*50 + "\n")
    print(comparison['lime_text'])
    
    # Get global feature importance
    global_importance = explainer.get_global_feature_importance()
    print("\n=== GLOBAL FEATURE IMPORTANCE ===\n")
    for feature, importance in list(global_importance.items())[:5]:
        print(f"{feature}: {importance:.4f}")