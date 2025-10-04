# HealthBench-BR Batch Evaluation System

## Estrutura Implementada

### 1. Arquivo de Configuração (`providers.json`)
Define todos os providers LLM que serão avaliados:

```json
{
  "providers": [
    {
      "name": "GPT-4o",
      "type": "openai",
      "model": "gpt-4o",
      "api_key": "${OPENAI_API_KEY}",
      "base_url": "https://api.openai.com/v1"
    },
    {
      "name": "Claude-Haiku-Bedrock",
      "type": "aws_bedrock",
      "model": "anthropic.claude-3-haiku-20240307-v1:0",
      "region": "us-east-1",
      "aws_bearer_token": "${AWS_BEARER_TOKEN_BEDROCK}"
    }
  ]
}
```

### 2. Módulos Criados

#### `src/config/loader.py`
- Carrega e valida configurações do `providers.json`
- Substitui variáveis de ambiente automaticamente
- Valida requisitos de cada provider

#### `src/providers/factory.py`
- Factory pattern para criar providers dinamicamente
- Suporta todos os tipos: openai, ollama, aws_bedrock, maritaca

#### `evaluate_batch.py`
- Script principal para executar avaliações em lote
- Executa todos os providers ou apenas os especificados
- Salva resultados individuais e resumo comparativo

### 3. Atualização no Bedrock Provider
- Adicionado suporte para `AWS_BEARER_TOKEN_BEDROCK`
- Mantém compatibilidade com credenciais AWS tradicionais

## Como Usar

### 1. Configurar Variáveis de Ambiente
```bash
export OPENAI_API_KEY="sua-chave-aqui"
export AWS_BEARER_TOKEN_BEDROCK="seu-token-aqui"
export MARITACA_API_KEY="sua-chave-aqui"
```

### 2. Executar Todos os Providers
```bash
python evaluate_batch.py --config providers.json
```

### 3. Executar Providers Específicos
```bash
python evaluate_batch.py --providers "GPT-4o" "Claude-Haiku-Bedrock"
```

### 4. Limitar Número de Perguntas (para testes)
```bash
python evaluate_batch.py --limit 10
```

## Estrutura de Saída

Os resultados são salvos em:
```
evaluation_results/
└── run_20240328_143022/
    ├── GPT-4o_results.csv
    ├── GPT-4o_detailed.json
    ├── Claude-Haiku-Bedrock_results.csv
    ├── Claude-Haiku-Bedrock_detailed.json
    ├── combined_summary.csv
    └── run_metadata.json
```

## Recursos Implementados

✅ **Configuração Centralizada**: Todos os providers em um único arquivo JSON  
✅ **Execução em Batch**: Avalia múltiplos modelos sequencialmente  
✅ **Substituição de Variáveis**: Suporta ${VAR_NAME} no JSON  
✅ **Validação Automática**: Verifica configurações antes de executar  
✅ **Relatórios Comparativos**: Gera resumo com métricas de todos os modelos  
✅ **Suporte AWS Bearer Token**: Usa AWS_BEARER_TOKEN_BEDROCK para Bedrock  
✅ **Persistência de Resultados**: Salva CSVs e JSONs detalhados  

## Próximos Passos Sugeridos

1. **Execução Paralela**: Executar múltiplos providers simultaneamente
2. **Dashboard Web**: Interface para visualizar comparações
3. **Métricas Adicionais**: Tempo de resposta, custo por token
4. **Configuração de Prompts**: Permitir diferentes prompts por provider
5. **Integração CI/CD**: Executar automaticamente em pipelines