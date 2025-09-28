# Makefile para avaliação de LLMs com evaluate.py

# Configurações padrão
PYTHON := python3
SCRIPT := evaluate.py
DATASET := benchmark_perguntas_unificado.json
PARALLELISM := 10
TEMPERATURE := 0.0
MAX_TOKENS := 12000

# API Keys (substitua com suas chaves)
SABIAZINHO_API_KEY := 100088405894968274443_7c358b001f0e8d55

# URLs das APIs
SABIAZINHO_URL := https://chat.maritaca.ai/api
OPENAI_URL := https://api.openai.com/v1
OLLAMA_URL := http://localhost:11434/v1

# Comando base
EVALUATE_CMD := $(PYTHON) $(SCRIPT)

# Targets principais
.PHONY: help evaluate-sabiazinho-3 evaluate-gpt-4 evaluate-ollama check-dataset clean

help:
	@echo "Comandos disponíveis:"
	@echo "  make evaluate-sabiazinho-3  - Avaliar com Sabiazinho-3"
	@echo "  make evaluate-gpt-4         - Avaliar com GPT-4 (requer OPENAI_API_KEY)"
	@echo "  make evaluate-ollama MODEL=<modelo> - Avaliar com Ollama local"
	@echo "  make check-dataset          - Verificar se dataset existe"
	@echo "  make clean                  - Limpar arquivos de resultado"
	@echo ""
	@echo "Variáveis configuráveis:"
	@echo "  LIMIT=100                   - Limitar número de perguntas"
	@echo "  PARALLELISM=5               - Número de chamadas paralelas"
	@echo "  TEMPERATURE=0.1             - Temperatura do modelo"

# Avaliar com Sabiazinho-3
evaluate-sabiazinho-3: check-dataset
	@echo "🤖 Avaliando com Sabiazinho-3..."
	@$(EVALUATE_CMD) \
		--model "sabiazinho-3" \
		--base_url "$(SABIAZINHO_URL)" \
		--api_key "$(SABIAZINHO_API_KEY)" \
		--dataset_path "$(DATASET)" \
		--parallelism $(PARALLELISM) \
		--temperature $(TEMPERATURE) \
		--max_tokens $(MAX_TOKENS) \
		--csv_out "resultados_sabiazinho3.csv" \
		$(if $(LIMIT),--limit $(LIMIT))

# Avaliar com GPT-4 (requer OPENAI_API_KEY no ambiente)
evaluate-gpt-4: check-dataset
	@if [ -z "$(OPENAI_API_KEY)" ]; then \
		echo "❌ Erro: OPENAI_API_KEY não definida"; \
		echo "Use: make evaluate-gpt-4 OPENAI_API_KEY=sk-..."; \
		exit 1; \
	fi
	@echo "🤖 Avaliando com GPT-4..."
	@$(EVALUATE_CMD) \
		--model "gpt-4" \
		--base_url "$(OPENAI_URL)" \
		--api_key "$(OPENAI_API_KEY)" \
		--dataset_path "$(DATASET)" \
		--parallelism $(PARALLELISM) \
		--temperature $(TEMPERATURE) \
		--max_tokens $(MAX_TOKENS) \
		--csv_out "resultados_gpt4.csv" \
		$(if $(LIMIT),--limit $(LIMIT))

# Avaliar com Ollama local
evaluate-ollama: check-dataset
	@if [ -z "$(MODEL)" ]; then \
		echo "❌ Erro: MODEL não definido"; \
		echo "Use: make evaluate-ollama MODEL=llama3.2:3b"; \
		exit 1; \
	fi
	@echo "🤖 Avaliando com Ollama ($(MODEL))..."
	@$(EVALUATE_CMD) \
		--model "$(MODEL)" \
		--base_url "$(OLLAMA_URL)" \
		--api_key "ollama" \
		--dataset_path "$(DATASET)" \
		--parallelism $(PARALLELISM) \
		--temperature $(TEMPERATURE) \
		--max_tokens $(MAX_TOKENS) \
		--csv_out "resultados_ollama_$(subst :,_,$(MODEL)).csv" \
		$(if $(LIMIT),--limit $(LIMIT))

# Verificar se o dataset existe
check-dataset:
	@if [ ! -f "$(DATASET)" ]; then \
		echo "⚠️  Aviso: Arquivo $(DATASET) não encontrado!"; \
		echo "📝 Criando exemplo de dataset..."; \
		echo '[{"arquivo": "exemplo.txt", "titulo": "Perguntas de Teste", "perguntas": ["O céu é azul?", "A água é sólida em temperatura ambiente?", "2+2 é igual a 4?", "A Terra é plana?"]}]' > $(DATASET); \
		echo "✅ Arquivo de exemplo criado: $(DATASET)"; \
		echo ""; \
	fi

# Limpar arquivos de resultado
clean:
	@echo "🧹 Limpando arquivos de resultado..."
	@rm -f resultados_*.csv
	@echo "✅ Arquivos removidos"

# Instalar dependências
install:
	@echo "📦 Instalando dependências..."
	@pip install openai>=1.30.0
	@echo "✅ Dependências instaladas"

# Comparar resultados de diferentes modelos
compare: 
	@echo "📊 Arquivos de resultado disponíveis:"
	@ls -lh resultados_*.csv 2>/dev/null || echo "Nenhum arquivo encontrado. Execute avaliações primeiro."

# Testes rápidos com limite pequeno
test-sabiazinho: 
	@make evaluate-sabiazinho-3 LIMIT=10

test-all:
	@echo "🧪 Testando todos os modelos com 10 perguntas..."
	@make evaluate-sabiazinho-3 LIMIT=10
	@if [ ! -z "$(OPENAI_API_KEY)" ]; then make evaluate-gpt-4 LIMIT=10; fi
	@if command -v ollama &> /dev/null; then make evaluate-ollama MODEL=llama3.2:3b LIMIT=10; fi

.DEFAULT_GOAL := help