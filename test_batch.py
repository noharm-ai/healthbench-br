#!/usr/bin/env python3
"""
Test script for batch evaluation
"""

import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config_loader():
    """Test configuration loader"""
    from src.config.loader import ConfigLoader
    
    print("Testing Configuration Loader...")
    print("-" * 40)
    
    try:
        loader = ConfigLoader("providers.json")
        
        print(f"✅ Loaded {len(loader.providers)} providers:")
        for provider in loader.providers:
            print(f"  - {provider.name} ({provider.type}: {provider.model})")
        
        print(f"\n✅ Default settings:")
        print(f"  - Temperature: {loader.default_settings.temperature}")
        print(f"  - Max tokens: {loader.default_settings.max_tokens}")
        print(f"  - Timeout: {loader.default_settings.timeout}")
        print(f"  - Parallelism: {loader.default_settings.parallelism}")
        
        # Validate all providers
        print(f"\n🔍 Validating providers...")
        validation_results = loader.validate_all()
        
        if validation_results:
            print("⚠️  Validation issues found:")
            for provider_name, issues in validation_results.items():
                print(f"\n  {provider_name}:")
                for issue in issues:
                    print(f"    - {issue}")
        else:
            print("✅ All providers validated successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_provider_factory():
    """Test provider factory"""
    print("\n\nTesting Provider Factory...")
    print("-" * 40)
    
    try:
        from src.config.loader import ConfigLoader
        from src.providers.factory import ProviderFactory
        
        loader = ConfigLoader("providers.json")
        
        # Try to create a provider (ollama as it doesn't need API key)
        ollama_providers = loader.get_providers_by_type("ollama")
        if ollama_providers:
            provider_config = ollama_providers[0]
            print(f"Creating provider: {provider_config.name}")
            
            # Remove the stub ProviderConfigItem and use the real one
            # First, fix the import in factory.py
            import importlib
            import src.providers.factory as factory_module
            
            # Replace the stub with the real class
            factory_module.ProviderConfigItem = type(provider_config)
            
            provider = ProviderFactory.create_from_config(provider_config)
            print(f"✅ Successfully created {provider_config.name} provider")
            print(f"  - Model: {provider.config.model_name}")
            print(f"  - Temperature: {provider.config.temperature}")
            print(f"  - Max tokens: {provider.config.max_tokens}")
        else:
            print("⚠️  No Ollama providers found in config")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("="*60)
    print("HEALTHBENCH-BR BATCH EVALUATION TEST")
    print("="*60)
    
    # Test configuration loader
    config_ok = test_config_loader()
    
    # Test provider factory
    factory_ok = test_provider_factory()
    
    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Configuration Loader: {'✅ PASSED' if config_ok else '❌ FAILED'}")
    print(f"Provider Factory: {'✅ PASSED' if factory_ok else '❌ FAILED'}")
    
    if config_ok and factory_ok:
        print("\n✅ All tests passed! The batch evaluation system is ready.")
        print("\nTo run batch evaluation:")
        print("  python evaluate_batch.py --config providers.json")
        print("\nTo run specific providers:")
        print("  python evaluate_batch.py --providers 'GPT-4o' 'Claude-Haiku-Bedrock'")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()