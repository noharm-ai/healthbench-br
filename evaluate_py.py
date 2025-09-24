#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate.py — Avalia LLMs num benchmark de Verdadeiro/Falso (pt-BR).

Mudanças:
- Usa --base_url (no cliente OpenAI é passado como base_url).
- Executa as chamadas em batches em paralelo, com paralelismo configurável (default: 10).

Assunções sobre o dataset:
1) O arquivo JSON 'benchmark_perguntas_unificado.json' está na mesma pasta deste script.
2) Estrutura do arquivo: lista de blocos com "arquivo", "titulo" e "perguntas" (list[str]).
3) Gabarito: as perguntas vêm em PARES sequenciais; para cada par:
   - perguntas[i]   -> VERDADEIRO
   - perguntas[i+1] -> FALSO
   Se houver quantidade ímpar, a última é ignorada.

Parsing:
- Captura a *primeira* ocorrência final de {Verdadeiro|Falso} varrendo de trás pra frente
  (implementado escolhendo o *último* match do regex).

Saídas:
- Acurácia no stdout
- CSV 'resultados_avaliacao.csv' com:
  arquivo, titulo, idx_local, pergunta, esperado, pred, correta, resposta_bruta
"""

import argparse
import json
import os
import re
import sys
import csv
import asyncio
from typing import List, Optional

# pip install openai>=1.30.0
try:
    from openai import AsyncOpenAI
except Exception as e:
    print("Erro: é necessário instalar o pacote 'openai' (pip install openai).")
    raise

SYSTEM_PROMPT = (
    "Você está sendo avaliado em um benchmark de VERDADEIRO ou FALSO (pt-BR).\n"
    "Explique brevemente se quiser, MAS OBRIGATORIAMENTE termine a mensagem com uma linha final EXATA:\n"
    "Resposta: Verdadeiro\n"
    "ou\n"
    "Resposta: Falso\n"
    "A linha 'Resposta:' DEVE aparecer exatamente assim, com 'Verdadeiro' ou 'Falso' no fim."
)

VER_REGEX = re.compile(r"\b(verdadeiro|falso)\b", re.IGNORECASE)


class QAItem:
    __slots__ = ("arquivo", "titulo", "pergunta", "esperado", "idx_local")
    def __init__(self, arquivo: str, titulo: str, pergunta: str, esperado: str, idx_local: int):
        self.arquivo = arquivo
        self.titulo = titulo
        self.pergunta = pergunta
        self.esperado = esperado  # 'Verdadeiro' | 'Falso'
        self.idx_local = idx_local


def load_dataset(path: str) -> List[QAItem]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    items: List[QAItem] = []
    for bloco in data:
        arquivo = bloco.get("arquivo", "")
        titulo = bloco.get("titulo", "")
        perguntas = bloco.get("perguntas", [])
        # Caminha em pares (0,1), (2,3), ...
        for i in range(0, len(perguntas) - 1, 2):
            items.append(QAItem(arquivo, titulo, perguntas[i],     "Verdadeiro", i))
            items.append(QAItem(arquivo, titulo, perguntas[i + 1], "Falso",      i + 1))
    return items


def parse_label_from_response(text: str) -> Optional[str]:
    """
    Pega a primeira ocorrência final (varrendo de trás pra frente) de Verdadeiro/Falso.
    Implementado escolhendo o último match do regex.
    """
    matches = list(VER_REGEX.finditer(text or ""))
    if not matches:
        return None
    last = matches[-1].group(1).strip().lower()
    return "Verdadeiro" if last.startswith("v") else "Falso"


async def call_model_async(
    client: AsyncOpenAI,
    model: str,
    pergunta: str,
    temperature: float = 0.0,
    max_tokens: int = 12000,
) -> str:
    """
    Chamada assíncrona ao endpoint /chat/completions compatível OpenAI.
    """
    resp = await client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": pergunta},
        ],
    )
    return (resp.choices[0].message.content or "").strip()


async def evaluate_batch(
    client: AsyncOpenAI,
    batch_items: List[QAItem],
    model: str,
    temperature: float,
    max_tokens: int,
    start_index: int,
):
    """
    Avalia um batch em paralelo: cria todas as tasks e aguarda com gather.
    Retorna (linhas_csv_batch, acertos_batch).
    """
    async def one(qi: QAItem):
        try:
            resposta = await call_model_async(
                client, model, qi.pergunta, temperature=temperature, max_tokens=max_tokens
            )
        except Exception as e:
            resposta = f"[ERRO NA CHAMADA]: {e}"
            pred = None
            correta = "0"
        else:
            pred = parse_label_from_response(resposta)
            correta = "1" if (pred == qi.esperado) else "0"
        row = [
            qi.arquivo,
            qi.titulo,
            str(qi.idx_local),
            qi.pergunta.replace("\n", " ").strip(),
            qi.esperado,
            pred or "",
            correta,
            (resposta or "").replace("\n", "\\n"),
        ]
        return row, (correta == "1")

    tasks = [one(qi) for qi in batch_items]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    linhas, acertos = [], 0
    for row, ok in results:
        linhas.append(row)
        acertos += 1 if ok else 0

    # Log simples de progresso
    print(f"[{start_index + len(batch_items)}] processadas (batch tamanho {len(batch_items)}).")
    return linhas, acertos


async def amain():
    parser = argparse.ArgumentParser(description="Avalia LLM em benchmark de Verdadeiro/Falso.")
    parser.add_argument("--model", required=True, help="Nome do modelo (ex.: sabia3.1)")
    parser.add_argument("--base_url", required=True, help="Base URL compatível com o cliente OpenAI")
    parser.add_argument("--api_key", required=True, help="Chave de API para o endpoint")
    parser.add_argument("--dataset_path", default="benchmark_perguntas_unificado.json", help="Caminho do JSON do benchmark")
    parser.add_argument("--limit", type=int, default=None, help="Opcional: limitar o número total de perguntas")
    parser.add_argument("--temperature", type=float, default=0.0, help="Temperatura da inferência (default: 0.0)")
    parser.add_argument("--max_tokens", type=int, default=12000, help="max_tokens por resposta (default: 4000)")
    parser.add_argument("--csv_out", default="resultados_avaliacao.csv", help="Arquivo CSV de saída")
    parser.add_argument("--parallelism", type=int, default=10, help="Tamanho do batch/paralelismo (default: 10)")
    args = parser.parse_args()

    # Cliente Async OpenAI compatível
    client = AsyncOpenAI(api_key=args.api_key, base_url=args.base_url)

    # Carrega dataset
    items = load_dataset(args.dataset_path)
    if args.limit is not None:
        items = items[: max(0, args.limit)]
    total = len(items)
    if total == 0:
        print("Nenhuma pergunta carregada. Verifique o JSON.")
        sys.exit(1)

    print(f"Total de perguntas a avaliar: {total}")
    header = ["arquivo", "titulo", "idx_local", "pergunta", "esperado", "pred", "correta", "resposta_bruta"]
    linhas_csv = [header]

    acertos_total = 0
    processed = 0

    # Processa em batches em paralelo (cada batch lança 'parallelism' tasks)
    p = max(1, int(args.parallelism))
    for i in range(0, total, p):
        batch = items[i : i + p]
        linhas_batch, acertos_batch = await evaluate_batch(
            client=client,
            batch_items=batch,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            start_index=i,
        )
        linhas_csv.extend(linhas_batch)
        acertos_total += acertos_batch
        processed += len(batch)
        print(f"Acurácia parcial: {acertos_total}/{processed} = {acertos_total/processed:.3f}")

    # Salva CSV
    with open(args.csv_out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(linhas_csv)

    acc = acertos_total / total
    print("\n=========== RESUMO ===========")
    print(f"Modelo:           {args.model}")
    print(f"Perguntas:        {total}")
    print(f"Acertos:          {acertos_total}")
    print(f"Acurácia:         {acc:.4f}")
    print(f"CSV salvo em:     {os.path.abspath(args.csv_out)}")


if __name__ == "__main__":
    asyncio.run(amain())
