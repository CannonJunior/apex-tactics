"""
Feature Flags for Migration Control

Controls which systems use the new architecture vs legacy implementation.
Allows safe rollback during migration.
"""

class FeatureFlags:
    """Central feature flag management for migration safety"""
    
    # Core Infrastructure
    USE_NEW_ACTION_SYSTEM = True
    USE_ACTION_QUEUE = True
    USE_EFFECT_SYSTEM = True
    USE_EVENT_BUS = True
    
    # Week 2 - Action System Integration
    USE_ACTION_MANAGER = True
    
    # Week 3 - AI Integration
    USE_MCP_TOOLS = True
    USE_AI_ORCHESTRATION = True
    
    # Week 4 - Queue Management UI
    USE_NEW_QUEUE_UI = True
    USE_PREDICTION_ENGINE = True
    
    # Performance
    USE_PARALLEL_AI = False
    USE_ACTION_CACHING = False
    
    @classmethod
    def is_legacy_mode(cls):
        """Check if running in full legacy mode"""
        return not any([
            cls.USE_NEW_ACTION_SYSTEM,
            cls.USE_ACTION_QUEUE,
            cls.USE_EFFECT_SYSTEM,
            cls.USE_MCP_TOOLS
        ])
    
    @classmethod
    def get_active_features(cls):
        """Get list of active new features"""
        features = []
        for attr in dir(cls):
            if attr.startswith('USE_') and getattr(cls, attr):
                features.append(attr)
        return features
    
    @classmethod
    def enable_feature(cls, feature_name: str):
        """Safely enable a feature"""
        if hasattr(cls, feature_name):
            setattr(cls, feature_name, True)
            print(f"✅ Enabled feature: {feature_name}")
        else:
            print(f"❌ Unknown feature: {feature_name}")
    
    @classmethod
    def disable_feature(cls, feature_name: str):
        """Safely disable a feature for rollback"""
        if hasattr(cls, feature_name):
            setattr(cls, feature_name, False)
            print(f"⏪ Disabled feature: {feature_name}")
        else:
            print(f"❌ Unknown feature: {feature_name}")
    
    @classmethod
    def rollback_all(cls):
        """Emergency rollback to full legacy mode"""
        for attr in dir(cls):
            if attr.startswith('USE_'):
                setattr(cls, attr, False)
        print("🚨 Emergency rollback: All features disabled")


# Global feature flag instance
FLAGS = FeatureFlags()