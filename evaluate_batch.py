#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HealthBench-BR Batch Evaluation Tool
Avalia múltiplos LLMs definidos em providers.json
"""

import argparse
import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.loader import ConfigLoader, ProviderConfigItem
from src.providers.factory import ProviderFactory
from src.dataset.loader import DatasetLoader
from src.evaluation.evaluator import Evaluator
from src.reports.generator import ReportGenerator


class BatchEvaluator:
    """Batch evaluator for multiple providers"""
    
    def __init__(self, config_path: str = "providers.json"):
        self.config_loader = ConfigLoader(config_path)
        self.results = {}
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    async def evaluate_provider(
        self,
        provider_config: ProviderConfigItem,
        dataset: List[Any],
        limit: Optional[int] = None,
        show_progress: bool = True
    ) -> Dict:
        """Evaluate a single provider"""
        
        print(f"\n{'='*60}")
        print(f"Evaluating: {provider_config.name}")
        print(f"Model: {provider_config.model}")
        print(f"Type: {provider_config.type}")
        print(f"{'='*60}\n")
        
        try:
            # Validate provider configuration
            issues = self.config_loader.validate_provider(provider_config)
            if issues:
                print(f"⚠️  Configuration issues for {provider_config.name}:")
                for issue in issues:
                    print(f"   - {issue}")
                return {
                    'provider': provider_config.name,
                    'model': provider_config.model,
                    'status': 'failed',
                    'error': '\n'.join(issues),
                    'results': []
                }
            
            # Create provider instance
            provider = ProviderFactory.create_from_config(provider_config)
            
            # Create evaluator
            evaluator = Evaluator(
                provider, 
                parallelism=self.config_loader.default_settings.parallelism
            )
            
            # Run evaluation
            results = await evaluator.evaluate(
                dataset,
                limit=limit,
                show_progress=show_progress
            )
            
            return {
                'provider': provider_config.name,
                'model': provider_config.model,
                'type': provider_config.type,
                'status': 'completed',
                'results': results,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Error evaluating {provider_config.name}: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'provider': provider_config.name,
                'model': provider_config.model,
                'status': 'failed',
                'error': str(e),
                'results': []
            }
    
    async def evaluate_all(
        self,
        dataset_path: str,
        providers: Optional[List[str]] = None,
        limit: Optional[int] = None,
        show_progress: bool = True
    ):
        """Evaluate all providers"""
        
        # Load dataset
        print(f"Loading dataset from {dataset_path}...")
        dataset = DatasetLoader.load_dataset(dataset_path)
        print(f"Dataset loaded: {len(dataset)} questions\n")
        
        # Select providers to evaluate
        if providers:
            # Filter specified providers
            selected_providers = []
            for name in providers:
                provider = self.config_loader.get_provider(name)
                if provider:
                    selected_providers.append(provider)
                else:
                    print(f"⚠️  Provider '{name}' not found in configuration")
        else:
            # Use all providers
            selected_providers = self.config_loader.providers
        
        if not selected_providers:
            print("❌ No providers to evaluate")
            return
        
        print(f"Will evaluate {len(selected_providers)} provider(s):")
        for p in selected_providers:
            print(f"  - {p.name} ({p.type}: {p.model})")
        
        # Evaluate each provider
        for provider_config in selected_providers:
            result = await self.evaluate_provider(
                provider_config,
                dataset,
                limit=limit,
                show_progress=show_progress
            )
            self.results[provider_config.name] = result
    
    def save_results(self, output_dir: str = "evaluation_results"):
        """Save evaluation results"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Create timestamp directory
        run_dir = output_path / f"run_{self.timestamp}"
        run_dir.mkdir(exist_ok=True)
        
        # Save individual provider results
        for provider_name, result in self.results.items():
            if result['status'] == 'completed' and result['results']:
                # Save CSV
                csv_path = run_dir / f"{provider_name.replace(' ', '_')}_results.csv"
                report_gen = ReportGenerator(output_path=str(csv_path))
                report_gen.add_results(result['results'])
                report_gen.save_csv()
                
                # Save detailed JSON
                json_path = run_dir / f"{provider_name.replace(' ', '_')}_detailed.json"
                report_gen.save_detailed_report(str(json_path))
                
                print(f"✅ Saved results for {provider_name} to {csv_path}")
        
        # Save combined summary
        self.save_combined_summary(run_dir)
        
        # Save run metadata
        metadata = {
            'timestamp': self.timestamp,
            'providers': list(self.results.keys()),
            'results': {
                name: {
                    'status': r['status'],
                    'error': r.get('error'),
                    'total_questions': len(r.get('results', [])),
                    'timestamp': r.get('timestamp')
                }
                for name, r in self.results.items()
            }
        }
        
        metadata_path = run_dir / "run_metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 All results saved to: {run_dir}")
        
        return run_dir
    
    def save_combined_summary(self, output_dir: Path):
        """Save combined summary of all providers"""
        
        summary_data = []
        
        for provider_name, result in self.results.items():
            if result['status'] == 'completed' and result['results']:
                # Calculate metrics
                total = len(result['results'])
                correct = sum(1 for r in result['results'] if r.get('correct', False))
                accuracy = (correct / total * 100) if total > 0 else 0
                
                # Calculate per-category accuracy
                category_stats = {}
                for r in result['results']:
                    cat = r.get('category', 'Unknown')
                    if cat not in category_stats:
                        category_stats[cat] = {'total': 0, 'correct': 0}
                    category_stats[cat]['total'] += 1
                    if r.get('correct', False):
                        category_stats[cat]['correct'] += 1
                
                summary_data.append({
                    'Provider': provider_name,
                    'Model': result['model'],
                    'Type': result['type'],
                    'Total Questions': total,
                    'Correct': correct,
                    'Accuracy (%)': round(accuracy, 2),
                    **{
                        f'{cat} Accuracy (%)': round(
                            stats['correct'] / stats['total'] * 100, 2
                        ) if stats['total'] > 0 else 0
                        for cat, stats in category_stats.items()
                    }
                })
            else:
                summary_data.append({
                    'Provider': provider_name,
                    'Model': result.get('model', 'N/A'),
                    'Status': result['status'],
                    'Error': result.get('error', 'N/A')
                })
        
        # Save as CSV
        if summary_data:
            df = pd.DataFrame(summary_data)
            csv_path = output_dir / "combined_summary.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8')
            print(f"✅ Saved combined summary to {csv_path}")
            
            # Print summary table
            print("\n" + "="*60)
            print("EVALUATION SUMMARY")
            print("="*60)
            print(df.to_string(index=False))
            print("="*60)
    
    def print_summary(self):
        """Print evaluation summary"""
        
        print("\n" + "="*60)
        print("BATCH EVALUATION COMPLETE")
        print("="*60)
        
        for provider_name, result in self.results.items():
            print(f"\n{provider_name}:")
            print(f"  Status: {result['status']}")
            
            if result['status'] == 'completed' and result['results']:
                total = len(result['results'])
                correct = sum(1 for r in result['results'] if r.get('correct', False))
                accuracy = (correct / total * 100) if total > 0 else 0
                
                print(f"  Total Questions: {total}")
                print(f"  Correct: {correct}")
                print(f"  Accuracy: {accuracy:.2f}%")
            elif result['status'] == 'failed':
                print(f"  Error: {result.get('error', 'Unknown error')}")


async def main():
    parser = argparse.ArgumentParser(
        description="Batch evaluation of multiple LLM providers",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--config",
        default="providers.json",
        help="Path to providers configuration file"
    )
    
    parser.add_argument(
        "--dataset",
        default="benchmark_perguntas_unificado.json",
        help="Path to benchmark dataset"
    )
    
    parser.add_argument(
        "--providers",
        nargs="+",
        help="Specific providers to evaluate (default: all)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of questions per provider"
    )
    
    parser.add_argument(
        "--output-dir",
        default="evaluation_results",
        help="Directory to save results"
    )
    
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable progress bars"
    )
    
    args = parser.parse_args()
    
    try:
        # Create batch evaluator
        evaluator = BatchEvaluator(args.config)
        
        # Run evaluations
        await evaluator.evaluate_all(
            dataset_path=args.dataset,
            providers=args.providers,
            limit=args.limit,
            show_progress=not args.no_progress
        )
        
        # Save results
        evaluator.save_results(args.output_dir)
        
        # Print summary
        evaluator.print_summary()
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())