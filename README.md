# HealthBench-BR 🇧🇷

**Dataset de avaliação para Large Language Models (LLMs) em Português do Brasil na área da saúde**

## 📋 Descrição

O HealthBench-BR é um benchmark especializado para avaliar a performance de modelos de linguagem em questões médicas e de saúde em português brasileiro. Utiliza um conjunto de perguntas Verdadeiro/Falso cuidadosamente elaboradas para testar o conhecimento e raciocínio dos modelos em contextos médicos.

### 🎯 Características Principais
- **Arquitetura Modular**: Sistema componentizado com suporte a múltiplos provedores LLM
- **Integração LangChain**: Utiliza LangChain para abstração e padronização
- **Multi-Provider**: Suporte para OpenAI, Maritaca/Sabiá, Ollama e AWS Bedrock
- **Avaliação Assíncrona**: Processamento paralelo para maior eficiência
- **Relatórios Detalhados**: Exportação em CSV e JSON com métricas completas

## 🏗️ Estrutura do Projeto

```
healthbench-br/
├── src/
│   ├── providers/          # Implementações dos provedores LLM
│   │   ├── base.py         # Classe base abstrata
│   │   ├── maritaca.py     # Provider Maritaca/Sabiá
│   │   ├── openai_provider.py  # Provider OpenAI
│   │   ├── ollama.py       # Provider Ollama
│   │   └── bedrock.py      # Provider AWS Bedrock
│   ├── dataset/            # Carregamento e parsing de dados
│   │   └── loader.py       # DatasetLoader e ResponseParser
│   ├── evaluation/         # Lógica de avaliação
│   │   └── evaluator.py    # Classe Evaluator principal
│   └── reports/            # Geração de relatórios
│       └── generator.py    # ReportGenerator
├── evaluate.py             # Script principal
├── evaluate_py.py          # Script legado (mantido para compatibilidade)
├── requirements.txt        # Dependências do projeto
└── benchmark_perguntas_unificado.json  # Dataset de perguntas
```

## 🚀 Instalação

### Pré-requisitos
- Python 3.8+
- pip

### Instalação das Dependências

```bash
pip install -r requirements.txt
```

### Dependências Principais
- `langchain` - Framework principal para LLMs
- `langchain-openai` - Integração com OpenAI e compatíveis
- `langchain-community` - Provedores da comunidade (Ollama)
- `langchain-aws` - Integração com AWS Bedrock
- `openai` - Cliente OpenAI
- `boto3` - SDK AWS (para Bedrock)
- `tqdm` - Barras de progresso
- `aiohttp` - Cliente HTTP assíncrono

## 📊 Dataset

### Formato do Arquivo
O dataset deve estar em formato JSON com a seguinte estrutura:

**`benchmark_perguntas_unificado.json`**
```json
[
  {
    "arquivo": "nome_do_arquivo.txt",
    "titulo": "Título do Conjunto de Perguntas",
    "perguntas": [
      "Pergunta que deve ser respondida como Verdadeiro",
      "Pergunta que deve ser respondida como Falso",
      "Outra pergunta Verdadeiro",
      "Outra pergunta Falso"
    ]
  }
]
```

**Importante**: As perguntas devem estar em pares sequenciais:
- Posição par (0, 2, 4...) = **Verdadeiro**
- Posição ímpar (1, 3, 5...) = **Falso**

## 💻 Uso

### Comando Básico

```bash
python evaluate.py --provider PROVIDER --model MODEL [opções]
```

### Parâmetros Principais

#### Obrigatórios
- `--provider`: Provedor LLM (`maritaca`, `openai`, `ollama`, `bedrock`)
- `--model`: Nome do modelo a usar

#### Configuração do Modelo
- `--temperature`: Temperatura da inferência (padrão: 0.0)
- `--max_tokens`: Máximo de tokens por resposta (padrão: 12000)
- `--timeout`: Timeout em segundos (padrão: 120)

#### Configuração da API
- `--api_key`: Chave de API (obrigatório para OpenAI/Maritaca)
- `--base_url`: URL base customizada (opcional)

#### AWS Bedrock
- `--aws_access_key_id`: AWS Access Key ID
- `--aws_secret_access_key`: AWS Secret Access Key
- `--aws_session_token`: AWS Session Token (opcional)
- `--aws_region`: Região AWS (padrão: us-east-1)

#### Dataset e Avaliação
- `--dataset_path`: Caminho para o arquivo JSON (padrão: benchmark_perguntas_unificado.json)
- `--limit`: Limitar número de perguntas a avaliar
- `--parallelism`: Número de chamadas paralelas (padrão: 10)

#### Saída
- `--csv_out`: Nome do arquivo CSV de saída (padrão: resultados_avaliacao.csv)
- `--detailed_report`: Gerar relatório detalhado em JSON
- `--no_progress`: Desabilitar barra de progresso

## 📝 Exemplos de Uso

### OpenAI (GPT-4)
```bash
python evaluate.py \
  --provider openai \
  --model gpt-4 \
  --api_key sk-... \
  --temperature 0.1 \
  --parallelism 5
```

### Maritaca/Sabiá
```bash
python evaluate.py \
  --provider maritaca \
  --model sabia-3 \
  --api_key sua_chave_maritaca \
  --base_url https://api.maritaca.ai/v1 \
  --limit 100
```

### Ollama (Local)
```bash
python evaluate.py \
  --provider ollama \
  --model llama3.2:3b \
  --base_url http://localhost:11434 \
  --parallelism 20
```

### AWS Bedrock (Claude)
```bash
python evaluate.py \
  --provider bedrock \
  --model claude-3-sonnet \
  --aws_access_key_id AKIAIOSFODNN7EXAMPLE \
  --aws_secret_access_key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
  --aws_region us-east-1 \
  --detailed_report
```

### Avaliação com Relatório Detalhado
```bash
python evaluate.py \
  --provider openai \
  --model gpt-3.5-turbo \
  --api_key sk-... \
  --dataset_path meu_dataset.json \
  --csv_out resultados_gpt35.csv \
  --detailed_report \
  --limit 50 \
  --parallelism 10
```

## 🔍 Formato de Resposta Esperado

O modelo deve responder seguindo o formato:
```
[Explicação opcional do modelo]

Resposta: Verdadeiro
```
ou
```
[Explicação opcional do modelo]

Resposta: Falso
```

O sistema extrai automaticamente a última ocorrência de "Verdadeiro" ou "Falso" na resposta.

## 📤 Saídas

### 1. Console
- Progresso em tempo real com barra de progresso
- Acurácia parcial durante execução
- Resumo final com métricas completas

### 2. Arquivo CSV (`resultados_avaliacao.csv`)
Contém as seguintes colunas:
- `arquivo`: Nome do arquivo fonte
- `titulo`: Título do conjunto
- `idx_local`: Índice da pergunta
- `pergunta`: Texto da pergunta
- `esperado`: Resposta correta
- `pred`: Predição do modelo
- `correta`: 1 se acertou, 0 se errou
- `resposta_bruta`: Resposta completa do modelo

### 3. Relatório JSON Detalhado (opcional)
Quando usar `--detailed_report`, gera arquivo JSON com:
- Timestamp da avaliação
- Métricas agregadas
- Métricas por arquivo
- Métricas por título
- Resultados completos de cada pergunta

## ⚡ Configuração de Performance

### Paralelismo
Ajuste `--parallelism` baseado no provider:
- **OpenAI/Maritaca**: 5-10 (respeitar rate limits)
- **Ollama (local)**: 20-50 (depende do hardware)
- **AWS Bedrock**: 10-20 (verificar cotas da região)

### Timeout
Ajuste `--timeout` para modelos mais lentos ou prompts complexos

## 🔧 Troubleshooting

### Erro de Importação
```bash
ImportError: No module named 'langchain'
```
**Solução**: Instalar dependências
```bash
pip install -r requirements.txt
```

### Erro de API Key
```bash
Erro: --api_key é obrigatório para o provider openai
```
**Solução**: Fornecer a chave de API apropriada

### Timeout em Modelos Locais
**Solução**: Aumentar o timeout
```bash
--timeout 300  # 5 minutos
```

### Rate Limit Exceeded
**Solução**: Reduzir paralelismo
```bash
--parallelism 3
```

## 🤝 Contribuição

Para contribuir com o projeto:

1. Adicionar novos providers em `src/providers/`
2. Estender a classe `BaseLLMProvider`
3. Implementar o método `initialize()`
4. Atualizar `evaluate.py` para incluir o novo provider
5. Adicionar dependências em `requirements.txt`
6. Documentar uso no README

## 📄 Licença

Este projeto está sob a licença especificada no arquivo [LICENSE](LICENSE).

## 🔄 Migração do Script Antigo

Se você estava usando o script `evaluate_py.py` anterior, migre para o novo sistema:

**Antes (antigo):**
```bash
python evaluate_py.py \
  --model sabia3.1 \
  --base_url https://api.maritaca.ai/v1 \
  --api_key KEY
```

**Agora (novo):**
```bash
python evaluate.py \
  --provider maritaca \
  --model sabia3.1 \
  --api_key KEY
```

### Principais Melhorias
- ✅ Suporte a múltiplos providers
- ✅ Arquitetura modular e extensível
- ✅ Integração com LangChain
- ✅ Melhor tratamento de erros
- ✅ Relatórios mais detalhados
- ✅ Código mais limpo e manutenível

## 👥 Autores

Desenvolvido para avaliação de LLMs em português brasileiro no contexto médico e de saúde.