"""Evaluation module using LangChain"""

import asyncio
from typing import List, Optional, Dict, Any
from tqdm.asyncio import tqdm
from src.providers.base import BaseLLMProvider
from src.dataset.loader import QAItem, ResponseParser
from src.reports.generator import EvaluationResult


SYSTEM_PROMPT = (
    "Você está sendo avaliado em um benchmark de VERDADEIRO ou FALSO (pt-BR).\n"
    "Explique brevemente se quiser, MAS OBRIGATORIAMENTE termine a mensagem com uma linha final EXATA:\n"
    "Resposta: Verdadeiro\n"
    "ou\n"
    "Resposta: Falso\n"
    "A linha 'Resposta:' DEVE aparecer exatamente assim, com 'Verdadeiro' ou 'Falso' no fim."
)


class Evaluator:
    """Main evaluator class using LangChain providers"""
    
    def __init__(self, provider: BaseLLMProvider, parallelism: int = 10):
        self.provider = provider
        self.parallelism = parallelism
        self.parser = ResponseParser()
    
    async def evaluate_single(self, item: QAItem) -> EvaluationResult:
        """Evaluate a single question"""
        try:
            response = await self.provider.ainvoke(SYSTEM_PROMPT, item.pergunta)
        except Exception as e:
            response = f"[ERRO NA CHAMADA]: {e}"
            pred = None
            correta = False
        else:
            pred, correta = self.parser.validate_response(response, item.esperado)
        
        return EvaluationResult(
            arquivo=item.arquivo,
            titulo=item.titulo,
            idx_local=item.idx_local,
            pergunta=item.pergunta,
            esperado=item.esperado,
            pred=pred,
            correta=correta,
            resposta_bruta=response
        )
    
    async def evaluate_batch(self, items: List[QAItem], show_progress: bool = True) -> List[EvaluationResult]:
        """Evaluate a batch of questions in parallel"""
        results = []
        
        # Process in chunks based on parallelism
        for i in range(0, len(items), self.parallelism):
            batch = items[i:i + self.parallelism]
            
            if show_progress:
                tasks = [self.evaluate_single(item) for item in batch]
                batch_results = await tqdm.gather(*tasks, desc=f"Batch {i//self.parallelism + 1}")
            else:
                tasks = [self.evaluate_single(item) for item in batch]
                batch_results = await asyncio.gather(*tasks)
            
            results.extend(batch_results)
            
            # Print partial accuracy
            correct = sum(1 for r in results if r.correta)
            total = len(results)
            print(f"Acurácia parcial: {correct}/{total} = {correct/total:.3f}")
        
        return results
    
    async def evaluate(self, items: List[QAItem], limit: Optional[int] = None, 
                       show_progress: bool = True) -> List[EvaluationResult]:
        """
        Evaluate all items
        
        Args:
            items: List of QAItems to evaluate
            limit: Optional limit on number of items to evaluate
            show_progress: Whether to show progress bar
            
        Returns:
            List of EvaluationResult objects
        """
        if limit:
            items = items[:limit]
        
        if len(items) == 0:
            print("Nenhuma pergunta para avaliar")
            return []
        
        print(f"Total de perguntas a avaliar: {len(items)}")
        return await self.evaluate_batch(items, show_progress)