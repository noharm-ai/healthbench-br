"""Report generation module"""

import csv
import os
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class EvaluationResult:
    """Result of a single evaluation"""
    arquivo: str
    titulo: str
    idx_local: int
    pergunta: str
    esperado: str
    pred: str
    correta: bool
    resposta_bruta: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for CSV output"""
        return {
            "arquivo": self.arquivo,
            "titulo": self.titulo,
            "idx_local": str(self.idx_local),
            "pergunta": self.pergunta.replace("\n", " ").strip(),
            "esperado": self.esperado,
            "pred": self.pred or "",
            "correta": "1" if self.correta else "0",
            "resposta_bruta": (self.resposta_bruta or "").replace("\n", "\\n")
        }


class ReportGenerator:
    """Generates evaluation reports and saves results"""
    
    def __init__(self, output_path: str = "resultados_avaliacao.csv"):
        self.output_path = output_path
        self.results: List[EvaluationResult] = []
    
    def add_result(self, result: EvaluationResult):
        """Add a single evaluation result"""
        self.results.append(result)
    
    def add_results(self, results: List[EvaluationResult]):
        """Add multiple evaluation results"""
        self.results.extend(results)
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate evaluation metrics"""
        total = len(self.results)
        if total == 0:
            return {
                "total": 0,
                "acertos": 0,
                "erros": 0,
                "acuracia": 0.0,
                "sem_resposta": 0
            }
        
        correct = sum(1 for r in self.results if r.correta)
        no_answer = sum(1 for r in self.results if r.pred is None or r.pred == "")
        
        return {
            "total": total,
            "acertos": correct,
            "erros": total - correct,
            "acuracia": correct / total,
            "sem_resposta": no_answer,
            "por_arquivo": self._metrics_by_file(),
            "por_titulo": self._metrics_by_title()
        }
    
    def _metrics_by_file(self) -> Dict[str, Dict[str, Any]]:
        """Calculate metrics grouped by file"""
        by_file = {}
        for result in self.results:
            if result.arquivo not in by_file:
                by_file[result.arquivo] = {"total": 0, "correct": 0}
            by_file[result.arquivo]["total"] += 1
            if result.correta:
                by_file[result.arquivo]["correct"] += 1
        
        for arquivo in by_file:
            total = by_file[arquivo]["total"]
            correct = by_file[arquivo]["correct"]
            by_file[arquivo]["accuracy"] = correct / total if total > 0 else 0
        
        return by_file
    
    def _metrics_by_title(self) -> Dict[str, Dict[str, Any]]:
        """Calculate metrics grouped by title"""
        by_title = {}
        for result in self.results:
            if result.titulo not in by_title:
                by_title[result.titulo] = {"total": 0, "correct": 0}
            by_title[result.titulo]["total"] += 1
            if result.correta:
                by_title[result.titulo]["correct"] += 1
        
        for titulo in by_title:
            total = by_title[titulo]["total"]
            correct = by_title[titulo]["correct"]
            by_title[titulo]["accuracy"] = correct / total if total > 0 else 0
        
        return by_title
    
    def save_csv(self):
        """Save results to CSV file"""
        if not self.results:
            print("Nenhum resultado para salvar")
            return
        
        fieldnames = [
            "arquivo", "titulo", "idx_local", "pergunta",
            "esperado", "pred", "correta", "resposta_bruta"
        ]
        
        with open(self.output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self.results:
                writer.writerow(result.to_dict())
        
        print(f"CSV salvo em: {os.path.abspath(self.output_path)}")
    
    def print_summary(self, model_name: str = ""):
        """Print evaluation summary"""
        metrics = self.calculate_metrics()
        
        print("\n" + "=" * 50)
        print(" " * 15 + "RESUMO DA AVALIAÇÃO")
        print("=" * 50)
        
        if model_name:
            print(f"Modelo:           {model_name}")
        print(f"Data:             {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total perguntas:  {metrics['total']}")
        print(f"Acertos:          {metrics['acertos']}")
        print(f"Erros:            {metrics['erros']}")
        print(f"Acurácia:         {metrics['acuracia']:.4f}")
        print(f"Sem resposta:     {metrics['sem_resposta']}")
        
        if metrics.get('por_arquivo'):
            print("\n" + "-" * 50)
            print("Acurácia por arquivo:")
            for arquivo, stats in metrics['por_arquivo'].items():
                print(f"  {arquivo}: {stats['accuracy']:.4f} ({stats['correct']}/{stats['total']})")
        
        print("=" * 50)
    
    def save_detailed_report(self, path: str = ""):
        """Save detailed JSON report"""
        if not path:
            path = self.output_path.replace('.csv', '_detailed.json')
        
        import json
        metrics = self.calculate_metrics()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "results": [asdict(r) for r in self.results]
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"Relatório detalhado salvo em: {os.path.abspath(path)}")