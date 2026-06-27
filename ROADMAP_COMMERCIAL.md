# BitNet CPU-Universal — Roadmap Comercial

> **Tese:** GPU é o mainframe do LLM. Ternary math + CPU é o futuro.
> **Meta:** Produto comercial, universal, air-gapped, sem GPU.

---

## Fase 0 — Fundação (Jun 2026) ✅

- [x] BitNet C++ com 5 níveis algébricos (L1-L5)
- [x] Inferência 1.58-bit CPU (I2_S, AVX2/NEON)
- [x] ACDC L3 (+144% Falcon3-3B)
- [x] BitNet Studio (server Python + MCP bridge)
- [x] Falcon3-3B fine-tuned CPU-only (150 steps, 58 min)
- [x] 10 ferramentas Protheus-RAG integradas
- [x] Parser robusto de tool_call (6 fallbacks)
- [x] Memória cross-agent (mem0)
- [x] README v3.0, CI, testes C++ (15/15)
- [x] Air-gapped testado

**Métrica inicial:** 38.9% acerto em tool-calling (72 testes)

---

## Fase 1 — Qualidade do tool-calling (Q3 2026) ✅

**Meta:** 80%+ acerto, confiável para uso real — **ATINGIDO: 91.7%**

### 1.1 Dataset v4 — formato correto ✅
- [x] Negativos com 4 mensagens (mesmo formato dos positivos)
- [x] 50+ exemplos negativos variados (casuais, matemática, off-topic)
- [x] 512 exemplos positivos (cobertura equilibrada por tool: 30-54 cada)
- [x] Exemplos multi-turn (pergunta → tool → resultado → resposta)
- [x] Exemplos 2-mensagens (tool call direta, sem tool_result) para tools mem0

### 1.2 Fine-tune v4 ✅
- [x] Treinar com dataset v4 (350 steps, seed=42, ~3.3h CPU)
- [x] Validar com test_50x_file.py (72 testes, greedy determinístico)
- [x] **Meta atingida: 91.7% acerto** (55/60), todas as 10 tools a 100%
- [x] Config otimizada: `min_new_tokens=25`, `do_sample=False`, `max_tokens=128`
- [ ] Pendente: negativos 50% → meta <5% falso positivo (dataset v5)

### 1.3 Parser v2 ✅
- [x] Suporte a múltiplas tool_calls em uma resposta (`parse_all_tool_calls`)
- [x] Detecção de "não precisa de tool" (`should_use_tool` com word boundaries)
- [x] Retry automático com prompt de correção (`build_retry_prompt`)
- [x] Normalização de nomes (dashes → underscores)
- [x] 26/26 testes unitários passando (100%)
- [x] Loop agentic integrado em `api.py` com retry e pre-filtro heurístico

### 1.4 Bugs críticos corrigidos ✅
- [x] Prompt ChatML no test_50x_file.py (`<|im_start|>`/`<|im_end|>`)
- [x] Extração de response (`<|im_start|>assistant` em vez de string inexistente)
- [x] `min_new_tokens` para evitar stop prematuro com `<|im_end|>`
- [x] `min_predict` integrado no `inference.py` (llama.cpp HTTP)

### Resultado detalhado 72x

| Categoria | Pass rate | Detalhe |
|-----------|-----------|--------|
| Tools de consulta | **100%** (25/25) | 5 tools × 5 iterações |
| Tools mem0 | **100%** (25/25) | 5 tools × 5 iterações |
| Negativos | **50%** (5/10) | 2 perguntas × 5 iterações |
| **Total** | **91.7%** (55/60) | Greedy determinístico |

---

## Fase 2 — Performance (Q4 2026)

**Meta:** Inferência 3B em <500ms/token em CPU consumer

### 2.1 Kernels
- [ ] L4 Tropical em produção (atenção esparsa max,+)
- [ ] L5 HRR para memória de longo contexto
- [ ] K_i8 cache otimizado
- [ ] Benchmark: Falcon3-3B vs GPU T4 (custo/benefício)

### 2.2 Quantização
- [ ] Merge adapter → modelo base
- [ ] Quantização pós-treino (GGUF Q4_K_M, Q5_K_M)
- [ ] Benchmark de qualidade por nível de quantização

### 2.3 Modelos suportados
- [ ] Falcon3-3B (atual)
- [ ] Falcon3-7B (se RAM > 16GB)
- [ ] Phi-3-mini (alternativa leve)
- [ ] Testar com modelos portugueses (sabia-3B, etc.)

---

## Fase 3 — Empacotamento (Q1 2027)

**Meta:** Instalável em 3 comandos, sem conhecimento técnico

### 3.1 Distribuição
- [ ] Docker image (`docker run bitnet-cpu`)
- [ ] CLI unificado (`bitnet serve`, `bitnet finetune`, `bitnet test`)
- [ ] Installer Linux (deb/rpm)
- [ ] Installer Windows (zip portable)
- [ ] Modelos pré-quantizados para download

### 3.2 Studio
- [ ] Web UI (React + Tailwind, roda local)
- [ ] Chat interface com tool-calling visível
- [ ] Configuração de MCP servers via UI
- [ ] Logs e métricas em tempo real

### 3.3 Documentação
- [ ] Quick start (5 min)
- [ ] Tutorial: integrar com Protheus
- [ ] Tutorial: criar nova ferramenta MCP
- [ ] Tutorial: fine-tune customizado
- [ ] API reference

---

## Fase 4 — Vertical Protheus (Q2 2027)

**Meta:** Primeiro cliente pagante no ecossistema TOTVS

### 4.1 Integração Protheus
- [ ] RAG completo: source AdvPL/TLPP → embeddings → busca
- [ ] Dicionário de dados completo (SX2, SX3, SIX, SX6, SXB)
- [ ] Geração de código AdvPL/TLPP assistida
- [ ] Análise de impacto de mudanças (cross-reference)

### 4.2 Casos de uso
- [ ] "Como funciona a função X?" → RAG + explicação
- [ ] "Quais campos tem a tabela Y?" → dicionário
- [ ] "Crie um ponto de entrada para Z" → geração de código
- [ ] "Quebra essa rotina em MVC" → refactoring assistido
- [ ] "Documenta este fonte" → ProtheusDOC automático

### 4.3 Go-to-market
- [ ] Piloto com 1 consultoria TOTVS
- [ ] Pricing: por usuário/mês (SaaS local) ou licença perpétua
- [ ] Case study: "Como a consultoria X reduziu 60% do tempo de análise de código"
- [ ] Apresentação no TOTVS Developer Conference

---

## Fase 5 — Universalidade (Q3 2027+)

**Meta:** BitNet CPU para qualquer ERP legacy

### 5.1 Verticais
- [ ] SAP ABAP (RAG + geração de código)
- [ ] Oracle PL/SQL (RAG + análise de packages)
- [ ] COBOL bancário (RAG + modernização)
- [ ] Java/C# enterprise (RAG + refactoring)

### 5.2 Plataforma
- [ ] SDK para criar conectores MCP (qualquer sistema)
- [ ] Marketplace de ferramentas
- [ ] Fine-tune como serviço (upload dataset → adapter)
- [ ] Model hub (modelos pré-treinados por vertical)

### 5.3 Comunidade
- [ ] Open core: kernel C++ open source (MIT)
- [ ] Studio: comercial (licença por organização)
- [ ] Comunidade de desenvolvedores de ferramentas
- [ ] Hackathon: "Melhor ferramenta MCP para BitNet"

---

## Métricas de sucesso

| Fase | Métrica | Meta |
|------|---------|------|
| F1 | Tool-calling accuracy | 80%+ → **91.7%** ✅ |
| F2 | Tokens/seg em CPU consumer | >2 tok/s (3B) |
| F3 | Tempo de instalação | <5 min |
| F4 | Primeiro cliente pagante | R$ 50k/ano |
| F5 | 3 verticais ativas | 100+ organizações |

---

## Principios fundadores (não negociáveis)

1. **CPU only** — GPU kernels nunca
2. **Air-gapped** — funciona sem internet, sempre
3. **Sem telemetria** — privacidade é feature
4. **Ternary math** — 1.58-bit é o caminho, não 4-bit ou 8-bit
5. **Open core** — kernel aberto, Studio comercial

---

*Criado em 2026-06-23. Atualizado em 2026-06-27 — Fase 1 concluída (91.7%).*
