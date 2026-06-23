# BitNet CPU-Universal — Roadmap Comercial

> **Tese:** GPU é o mainframe do LLM. Ternary math + CPU é o futuro.
> **Meta:** Produto comercial, universal, air-gapped, sem GPU.

---

## Fase 0 — Onde estamos (Jun 2026) ✅

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

**Métrica atual:** 38.9% acerto em tool-calling (72 testes)

---

## Fase 1 — Qualidade do tool-calling (Q3 2026)

**Meta:** 80%+ acerto, confiável para uso real

### 1.1 Dataset v3 — formato correto
- [ ] Negativos com 4 mensagens (mesmo formato dos positivos)
- [ ] 50+ exemplos negativos variados (casuais, matemática, off-topic)
- [ ] 200+ exemplos positivos (aumentar cobertura por tool)
- [ ] Exemplos multi-turn (pergunta → tool → resultado → resposta)

### 1.2 Fine-tune v3
- [ ] Treinar com dataset v3 (200+ steps)
- [ ] Validar com test_50x_file.py
- [ ] Meta: 80%+ acerto, <5% falso positivo

### 1.3 Parser v2
- [ ] Suporte a múltiplas tool_calls em uma resposta
- [ ] Detecção de "não precisa de tool" (confiança)
- [ ] Retry automático com prompt de correção

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
| F1 | Tool-calling accuracy | 80%+ |
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

*Criado em 2026-06-23. Vivo — atualizar a cada fase concluída.*
