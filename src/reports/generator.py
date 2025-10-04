"""Report generation module"""

import csv
import os
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import json


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
        
        metrics = self.calculate_metrics()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "results": [asdict(r) for r in self.results]
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"Relatório detalhado salvo em: {os.path.abspath(path)}")
    
    def save_html_report(self, path: str = "", model_name: str = ""):
        """Save HTML report"""
        if not path:
            path = self.output_path.replace('.csv', '_report.html')
        
        metrics = self.calculate_metrics()
        
        html_content = self._generate_html_report(metrics, model_name)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"Relatório HTML salvo em: {os.path.abspath(path)}")
    
    def _generate_html_report(self, metrics: Dict[str, Any], model_name: str = "") -> str:
        """Generate HTML report content"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Avaliação - HealthBench BR</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .summary {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .summary h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin: 0;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
            margin: 5px 0 0 0;
        }}
        .accuracy-bar {{
            width: 100%;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            margin: 10px 0;
            overflow: hidden;
        }}
        .accuracy-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 10px;
            transition: width 0.5s ease;
        }}
        .breakdown {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .breakdown h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .breakdown-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        .breakdown-table th,
        .breakdown-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .breakdown-table th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #667eea;
        }}
        .breakdown-table tr:hover {{
            background: #f8f9fa;
        }}
        .results {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .results h2 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
            margin-top: 0;
        }}
        .result-item {{
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            margin: 15px 0;
            padding: 20px;
            background: #fafafa;
        }}
        .result-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .result-title {{
            font-weight: bold;
            color: #333;
        }}
        .result-status {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .status-correct {{
            background: #d4edda;
            color: #155724;
        }}
        .status-incorrect {{
            background: #f8d7da;
            color: #721c24;
        }}
        .result-content {{
            margin: 10px 0;
        }}
        .result-label {{
            font-weight: bold;
            color: #555;
            margin-top: 15px;
        }}
        .result-text {{
            margin: 5px 0;
            padding: 10px;
            background: white;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }}
        @media (max-width: 768px) {{
            .metrics-grid {{
                grid-template-columns: 1fr;
            }}
            .result-header {{
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>HealthBench BR - Relatório de Avaliação</h1>
        <p>Avaliação de Modelos de Linguagem para Questões Médicas em Português</p>
    </div>

    <div class="summary">
        <h2>Resumo Geral</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value">{metrics['total']}</div>
                <div class="metric-label">Total de Perguntas</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['acertos']}</div>
                <div class="metric-label">Acertos</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['erros']}</div>
                <div class="metric-label">Erros</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{metrics['acuracia']:.2%}</div>
                <div class="metric-label">Acurácia</div>
            </div>
        </div>
        
        <div class="accuracy-bar">
            <div class="accuracy-fill" style="width: {metrics['acuracia']*100:.1f}%"></div>
        </div>
        
        <p><strong>Modelo:</strong> {model_name if model_name else 'N/A'}</p>
        <p><strong>Data da Avaliação:</strong> {timestamp}</p>
        <p><strong>Respostas sem conteúdo:</strong> {metrics['sem_resposta']}</p>
    </div>
"""
        
        # Add breakdown by file if available
        if metrics.get('por_arquivo'):
            html += """
    <div class="breakdown">
        <h2>Desempenho por Arquivo</h2>
        <table class="breakdown-table">
            <thead>
                <tr>
                    <th>Arquivo</th>
                    <th>Total</th>
                    <th>Acertos</th>
                    <th>Acurácia</th>
                </tr>
            </thead>
            <tbody>
"""
            for arquivo, stats in metrics['por_arquivo'].items():
                html += f"""
                <tr>
                    <td>{arquivo}</td>
                    <td>{stats['total']}</td>
                    <td>{stats['correct']}</td>
                    <td>{stats['accuracy']:.2%}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""
        
        # Add breakdown by title if available
        if metrics.get('por_titulo'):
            html += """
    <div class="breakdown">
        <h2>Desempenho por Categoria</h2>
        <table class="breakdown-table">
            <thead>
                <tr>
                    <th>Categoria</th>
                    <th>Total</th>
                    <th>Acertos</th>
                    <th>Acurácia</th>
                </tr>
            </thead>
            <tbody>
"""
            for titulo, stats in metrics['por_titulo'].items():
                html += f"""
                <tr>
                    <td>{titulo}</td>
                    <td>{stats['total']}</td>
                    <td>{stats['correct']}</td>
                    <td>{stats['accuracy']:.2%}</td>
                </tr>
"""
            html += """
            </tbody>
        </table>
    </div>
"""
        
        # Add detailed results (show first 10 for performance)
        html += """
    <div class="results">
        <h2>Resultados Detalhados (Primeiros 10)</h2>
"""
        
        for i, result in enumerate(self.results[:10]):
            status_class = "status-correct" if result.correta else "status-incorrect"
            status_text = "Correto" if result.correta else "Incorreto"
            
            html += f"""
        <div class="result-item">
            <div class="result-header">
                <div class="result-title">{result.titulo} - Item {result.idx_local}</div>
                <div class="result-status {status_class}">{status_text}</div>
            </div>
            <div class="result-content">
                <div class="result-label">Pergunta:</div>
                <div class="result-text">{result.pergunta}</div>
                
                <div class="result-label">Resposta Esperada:</div>
                <div class="result-text">{result.esperado}</div>
                
                <div class="result-label">Resposta do Modelo:</div>
                <div class="result-text">{result.pred or 'Sem resposta'}</div>
            </div>
        </div>
"""
        
        if len(self.results) > 10:
            html += f"""
        <p><em>Mostrando 10 de {len(self.results)} resultados. Para ver todos os resultados, consulte o arquivo CSV gerado.</em></p>
"""
        
        html += """
    </div>
</body>
</html>"""
        
        return html