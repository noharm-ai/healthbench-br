#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HealthBench-BR Evaluation Tool
Avalia LLMs num benchmark de Verdadeiro/Falso (pt-BR) usando LangChain
"""

import argparse
import asyncio
import sys
import os
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.providers.base import ProviderConfig
from src.providers.maritaca import MaritacaProvider
from src.providers.openai_provider import OpenAIProvider
from src.providers.ollama import OllamaProvider
from src.providers.bedrock import BedrockProvider
from src.dataset.loader import DatasetLoader
from src.evaluation.evaluator import Evaluator
from src.reports.generator import ReportGenerator


def get_provider(args):
    """Get the appropriate provider based on arguments"""
    
    # Create provider config
    config = ProviderConfig(
        model_name=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        api_key=args.api_key,
        base_url=args.base_url,
        timeout=args.timeout
    )
    
    # Select provider based on provider type
    if args.provider == "maritaca":
        return MaritacaProvider(config)
    elif args.provider == "openai":
        return OpenAIProvider(config)
    elif args.provider == "ollama":
        return OllamaProvider(config)
    elif args.provider == "bedrock":
        # Bedrock requires additional AWS credentials
        return BedrockProvider(
            config,
            aws_access_key_id=args.aws_access_key_id,
            aws_secret_access_key=args.aws_secret_access_key,
            aws_session_token=args.aws_session_token,
            region_name=args.aws_region
        )
    else:
        raise ValueError(f"Provider não suportado: {args.provider}")


async def main():
    parser = argparse.ArgumentParser(
        description="Avalia LLM em benchmark de Verdadeiro/Falso usando LangChain",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Provider selection
    parser.add_argument(
        "--provider",
        choices=["maritaca", "openai", "ollama", "bedrock"],
        required=True,
        help="Provedor LLM a usar"
    )
    
    # Model configuration
    parser.add_argument("--model", required=True, help="Nome do modelo")
    parser.add_argument("--temperature", type=float, default=0.0, help="Temperatura da inferência")
    parser.add_argument("--max_tokens", type=int, default=12000, help="Máximo de tokens por resposta")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout em segundos")
    
    # API configuration
    parser.add_argument("--api_key", help="Chave de API (não necessário para Ollama)")
    parser.add_argument("--base_url", help="URL base da API (opcional)")
    
    # AWS Bedrock specific
    parser.add_argument("--aws_access_key_id", help="AWS Access Key ID (para Bedrock)")
    parser.add_argument("--aws_secret_access_key", help="AWS Secret Access Key (para Bedrock)")
    parser.add_argument("--aws_session_token", help="AWS Session Token (para Bedrock, opcional)")
    parser.add_argument("--aws_region", default="us-east-1", help="AWS Region (para Bedrock)")
    
    # Dataset and evaluation
    parser.add_argument(
        "--dataset_path",
        default="benchmark_perguntas_unificado.json",
        help="Caminho do JSON do benchmark"
    )
    parser.add_argument("--limit", type=int, help="Limitar número de perguntas")
    parser.add_argument("--parallelism", type=int, default=10, help="Número de chamadas paralelas")
    
    # Output
    parser.add_argument("--csv_out", default="resultados_avaliacao.csv", help="Arquivo CSV de saída")
    parser.add_argument("--detailed_report", action="store_true", help="Gerar relatório detalhado JSON")
    parser.add_argument("--no_progress", action="store_true", help="Desabilitar barra de progresso")
    
    args = parser.parse_args()
    
    # Validate required arguments for specific providers
    if args.provider in ["maritaca", "openai"] and not args.api_key:
        print(f"Erro: --api_key é obrigatório para o provider {args.provider}")
        sys.exit(1)
    
    if args.provider == "bedrock":
        if not args.aws_access_key_id or not args.aws_secret_access_key:
            print("Nota: Credenciais AWS não fornecidas. Tentando usar credenciais do ambiente/perfil.")
    
    try:
        # Load dataset
        print(f"Carregando dataset de {args.dataset_path}...")
        dataset = DatasetLoader.load_dataset(args.dataset_path)
        print(f"Dataset carregado: {len(dataset)} perguntas")
        
        # Get provider
        print(f"Inicializando provider {args.provider}...")
        provider = get_provider(args)
        
        # Create evaluator
        evaluator = Evaluator(provider, parallelism=args.parallelism)
        
        # Run evaluation
        print("Iniciando avaliação...")
        results = await evaluator.evaluate(
            dataset,
            limit=args.limit,
            show_progress=not args.no_progress
        )
        
        # Generate reports
        print("\nGerando relatórios...")
        report_gen = ReportGenerator(output_path=args.csv_out)
        report_gen.add_results(results)
        
        # Save CSV
        report_gen.save_csv()
        
        # Save detailed report if requested
        if args.detailed_report:
            report_gen.save_detailed_report()
        
        # Print summary
        report_gen.print_summary(model_name=args.model)
        
    except FileNotFoundError as e:
        print(f"Erro: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Erro de configuração: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())