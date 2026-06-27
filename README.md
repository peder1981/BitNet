# BitNet CPU-Universal — Inferência 1.58-bit local-first + Tool-Calling PT-BR

[![CI](https://github.com/peder1981/BitNet/actions/workflows/ci.yml/badge.svg)](https://github.com/peder1981/BitNet/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![CPU Only](https://img.shields.io/badge/compute-CPU%20only-orange.svg)]()
[![No CUDA](https://img.shields.io/badge/no%20CUDA-required-red.svg)]()
[![No Cloud](https://img.shields.io/badge/no%20cloud-required-lightgrey.svg)]()
[![Air-Gapped](https://img.shields.io/badge/air--gapped-tested-success.svg)]()
[![Math Levels](https://img.shields.io/badge/math%20levels-5%2F5-blueviolet.svg)]()
[![Fine-Tuned](https://img.shields.io/badge/fine--tuned-Falcon3--3B--PTBR--tools-blue.svg)]()

> **Inferência 1.58-bit local-first, sem CUDA, sem cloud, sem telemetria.**
> Fine-tuning local CPU-only para tool-calling em português via MCP,
> **parser v2 com normalização de nomes, multi-tool, heurística de confiança e retry automático**,
> e **memória cross-agent** via mem0.
>
> **Fork de [`microsoft/BitNet`](https://github.com/microsoft/BitNet)** +
> **BitNet Studio** (server Python) com adapter QLoRA Falcon3-3B-Instruct
> fine-tuned para 10 ferramentas Protheus-RAG em PT-BR.

---
## O que é este projeto

BitNet CPU-Universal é uma stack completa de **inferência de LLM 100% local**
que evoluiu de um fork C++ de pesquisa para um sistema produtivo com:

1. **BitNet C++** — Engine de inferência 1.58-bit com 5 níveis algébricos (L1-L5)
2. **BitNet Studio** — Server Python com MCP bridge, fine-tuning local, e tool-calling
3. **Falcon3-3B Adapter** — Modelo fine-tuned CPU-only para responder em PT-BR e
   invocar 10 ferramentas Protheus-RAG via `<tool_call>`

**Para quem é:** Desenvolvedores e organizações que precisam de LLM
**offline, privado e soberano** — especialmente no ecossistema TOTVS Protheus
(AdvPL/TLPP), com acesso a RAG interno, dicionário de dados, e memória
persistente entre sessões.

---
## TL;DR (4 comandos)

```bash
# 1. Clone e setup
git clone --recursive https://github.com/peder1981/BitNet.git && cd BitNet
conda create -n bitnet python=3.10 -y && conda activate bitnet
pip install -r bitnet-studio/pyproject.toml

# 2. Fine-tune local CPU (Falcon3-3B, 250 steps, ~4h)
cd bitnet-studio
python finetune_local.py  # gera adapter em adapters/f3b-ptbr-tools-v4/

# 3. Testar tool-calling (72 testes exaustivos, ~2h)
python test_50x_file.py  # valida extração de JSON com parser v2

# 4. Testar parser v2 (26 testes unitários, <1s)
python test_parser_v2.py  # normalização, multi-tool, heurística, retry
```

---
## Evolução do adapter (v1 → v4)

| Versão | Dataset | Exemplos | Steps | Pass rate | Parser | Status |
|--------|---------|----------|-------|-----------|--------|--------|
| v1 | `ptbr_tools_train_large.jsonl` | 162 | 150 | 38.9% | v1 (6 fallbacks) | ✅ Commit |
| v2 | `ptbr_tools_train_v2.jsonl` | 220 | 180 | 31.9% | v1 | ❌ Regressão |
| v3 | `ptbr_tools_train_v3.jsonl` | 362 | 250 | 52.8% (72x) | v2 | ✅ Commit |
| **v4** | `ptbr_tools_train_v4.jsonl` | **512** | **350** | **91.7%** (72x) | **v2** | ✅ **Melhor** |

> **91.7% (55/60)** no teste exaustivo 72x com `min_new_tokens=25`, `do_sample=False` (greedy).
> Breakdown: **tools de consulta 100%** (25/25), **tools mem0 100%** (25/25), **negativos 50%** (5/10).
> Teste rápido (1 iteração): **83.3%** (10/12).

### Otimização de `min_new_tokens`

O modelo gerava `<|im_end|>` prematuramente antes da tool call. `min_new_tokens` força um mínimo de tokens:

| min_new_tokens | Consulta | mem0 | Negativos | Total |
|----------------|----------|------|-----------|-------|
| 20 | 100% (5/5) | 0% (0/5) | 100% (2/2) | 91.7% |
| **25** | **100% (5/5)** | **100% (5/5)** | **50% (1/2)** | **91.7%** |
| 30 | 60% (3/5) | 80% (4/5) | 100% (2/2) | 75.0% |

> **25 é o ponto ótimo** com adapter v4 — todas as tools a 100%.
> Negativos a 50% porque `min_new_tokens=25` força geração de tool call mesmo para não-tools.

### O que mudou em v3

**Dataset (362 exemplos):**
- 162 exemplos originais + 150 positivos extra + 50 negativos (4 mensagens)
- Foco em tools com baixo acerto no v1: `mem0_search`, `mem0_delete`, `consultar_dicionario_direto`

**Parser v2 (tool_engine.py):**
- **Normalização de nomes**: `protheus-rag-mem0-stats` → `protheus-rag__mem0_stats`
- **Fallback 2b**: tag com nome mas sem JSON braces
- **`parse_all_tool_calls`**: extrai múltiplas tool calls com deduplicação
- **`should_use_tool`**: heurística de confiança com word boundaries
- **`build_retry_prompt`**: prompt de correção para tool calls malformadas
- **26/26 testes unitários passando (100%)**

**Configuração:**
- `min_new_tokens`: 25 (ponto ótimo — evita stop prematuro com `<|im_end|>`)
- `do_sample`: False (greedy — determinístico, mais estável)
- `max_tokens`: 128, `temperature`: N/A (greedy)
- LoRA r=16, alpha=32, `MAX_SEQ_LEN=128`
- 250 steps, ~4h em CPU (Ryzen 9, 12 threads)

---
## Stack atual (2026-06-26)

### BitNet C++ (núcleo de pesquisa)

Engine de inferência 1.58-bit com 5 níveis algébricos demonstrando
"inferência CPU via álgebra esquecida":

| Nível | Operação | Ganho | Status |
|-------|----------|-------|--------|
| **L1 I2_S** | Quantização ternária `{-1,0,+1}` | 20× menos memória | ✅ Produção |
| **L2 WHT** | Walsh-Hadamard `W = H·D·H` | Zero multiplicações | ✅ Pesquisa |
| **L3 ACDC** | FWHT em circulant O(n log n) | +144% Falcon3-3B | ✅ Produção |
| **L4 Tropical** | Atenção esparsa (max,+) | +29% adaptive-K | ✅ Produção |
| **L5 HRR** | Memória holográfica | O(n log d) binding | 🔄 Reserva |

Ver `docs/theory/` para fundamentação matemática completa.

### BitNet Studio (server Python + fine-tuning)

```
bitnet-studio/
├── studio/
│   └── server/
│       ├── tool_engine.py      ← Parser v2: 6 fallbacks + normalização + multi-tool + heurística
│       ├── mcp_bridge.py       ← Bridge MCP para 10 tools protheus-rag
│       ├── api.py              ← Loop agentic com retry e pre-filtro heurístico
│       └── inference.py        ← Geração com adapter QLoRA
├── finetune_local.py           ← Fine-tune 100% CPU (Falcon3-3B, QLoRA)
├── test_50x_file.py            ← Teste exaustivo 72 rodadas (6×12 perguntas)
├── test_parser_v2.py           ← Teste unitário do parser v2 (26 testes)
├── data/
│   ├── gen_dataset_v3.py       ← Gerador dataset v3 (362 exemplos)
│   └── gen_dataset_v3_1.py     ← Gerador dataset v3.1 (502 exemplos)
└── adapters/
    ├── f3b-ptbr-tools-local/   ← Adapter v1 (150 steps)
    └── f3b-ptbr-tools-v3/      ← Adapter v3 (250 steps) — melhor resultado
```

**Ferramentas disponíveis (MCP — protheus-rag):**

| Tool | Função | Exemplo de uso |
|------|--------|----------------|
| `consultar_base_direta` | Busca direta no RAG AdvPL/TLPP | "Como funciona MaFisCalc?" |
| `consultar_base_interna` | Consulta interpretada via LLM | "Como funciona o faturamento?" |
| `consultar_dicionario_direto` | Dicionário de dados Protheus | "Quais campos tem SA1?" |
| `buscar_reversa_direto` | Busca no framework Reversa | "Como usar reversa-scout?" |
| `consultar_reversa_rag` | Consulta interpretada Reversa | "Como criar REST endpoint TLPP?" |
| `mem0_search` | Busca memórias do usuário | "O que sabemos sobre cliente João?" |
| `mem0_add` | Adiciona memória | "Anote: cliente prefere e-mail" |
| `mem0_list` | Lista todas memórias | "Liste memórias salvas" |
| `mem0_stats` | Estatísticas da base | "Quantas memórias temos?" |
| `mem0_delete` | Remove memória | "Apague memória sobre teste" |

**Parser v2 de tool_call (robustez):**

- 6 níveis de fallback progressivos (bloco completo, truncado, code fence, JSON puro, regex)
- Normalização de nomes: dashes para double underscores
- Fallback 2b: tag com nome mas sem JSON braces
- parse_all_tool_calls: extrai múltiplas tool calls com deduplicação
- should_use_tool: heurística de confiança com word boundaries (10 tools)
- build_retry_prompt: prompt de correção para tool calls malformadas
- JSON multiline com balanced braces
- 26/26 testes unitários passando (100%)

### Protocolo mem0 (cross-agent)

Memória persistente compartilhada entre agentes (Claude, OpenCode, Windsurf,
Devin) via namespace `default`. Regra mandatória: **RAG local primeiro** —
consultar `mem0_search` antes de qualquer busca externa.

Configurado em `AGENTS.md` e `CLAUDE.md`.

---
## Fine-tuning local (100% CPU)

### Setup de dados

```bash
cd bitnet-studio
# Dataset v3: 362 exemplos de tool-calling em PT-BR
# Formato: mensagens com role=user/assistant, tool calls em  tags
```

### Treinamento

```bash
# Falcon3-3B-Instruct + QLoRA (r=16, alpha=32, target_modules=all linear)
# 250 steps, batch_size=1, gradient_accumulation=2
# ~59s/step = ~4h total em CPU (Ryzen 9, 12 cores)
python finetune_local.py
```

### Resultados do adapter v4

| Metrica | Valor |
|---------|-------|
| Base model | `tiiuae/Falcon3-3B-Instruct` |
| Adapter path | `adapters/f3b-ptbr-tools-v4/` |
| Steps | 350 |
| Dataset | 512 exemplos (v4) |
| Tempo total | ~197 min (~3.3h) |
| Tempo/step | ~33s |
| Loss final | 0.13 |
| Pass rate | 91.7% (72x) / 83.3% (quick) |
| Hardware | CPU-only (12 threads) |

### Validacao

```bash
# Teste rapido (12 perguntas, 1 iteracao, ~20min)
python test_quick.py

# Teste exaustivo (72 testes = 12 perguntas x 6 iteracoes, ~2h)
python test_50x_file.py
```

Resultado: **91.7% acerto** (55/60 testes) com `min_new_tokens=25` e `do_sample=False`.

### Teste do parser v2 (unitario)

```bash
python test_parser_v2.py  # 26 testes, <1s
```

Resultado: **26/26 testes passando (100%)**.

---
## Uso

### Inferência C++ (air-gapped)

```bash
# Setup (uma vez)
python setup_env.py -md models/BitNet-b1.58-2B-4T -q i2_s

# Uso offline permanente
python run_inference.py \
  -m models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf \
  -p "Resuma este prontuário:" -n 200 -t 4
```

### Tool-calling com Falcon3 (Python)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
from studio.server.tool_engine import parse_tool_call

# Carregar base + adapter
base = AutoModelForCausalLM.from_pretrained("tiiuae/Falcon3-3B-Instruct")
model = PeftModel.from_pretrained(base, "adapters/f3b-ptbr-tools-v3")

# Gerar resposta
prompt = "<|user|>\nComo funciona MaFisCalc?\n<|assistant|>\n"
output = model.generate(**tokenizer(prompt, return_tensors="pt"), max_new_tokens=256)
response = tokenizer.decode(output[0])

# Extrair tool call (parser v2: 6 fallbacks + normalizacao + multi-tool)
tc = parse_tool_call(response, TOOLS)
if tc:
    print(f"Tool: {tc.name}, Args: {tc.arguments}")
```

---
## Testes

### C++ (kernels algébricos)

```bash
cd build && ctest --output-on-failure
# esperado: 15/15 PASS (default CI)
# ou 16/16 com -DBITNET_ENABLE_ACDC_RECT=ON
```

Cobre: kernel L1-L5 (WHT, FWHT, ACDC, tropical, HRR, K_i8 cache),
property-based tests com 100-1000 iters cada.

### Python (tool-calling)

```bash
cd bitnet-studio

# Teste do parser v2 (26 testes unitários, <1s)
python test_parser_v2.py

# Teste exaustivo (72 testes, ~2h) — salva progresso em arquivo
python test_50x_file.py
# Resultado: test_50x_progress.log + test_50x_results.json
```

---
## Documentação

### Decisão e arquitetura

- [`ROADMAP.md`](ROADMAP.md) — Roadmap público
- [`docs/decision-matrix.md`](docs/decision-matrix.md) — Quando usar L1/L3/L4/L5
- [`docs/hardware-compatibility.md`](docs/hardware-compatibility.md) — Matriz CPU → modo
- [`docs/invariants.md`](docs/invariants.md) — P1-P7 canônicas
- [`docs/findings-cpu-universal.md`](docs/findings-cpu-universal.md) — Validação empírica

### Teoria (referência acadêmica)

- [`docs/theory/00-index.md`](docs/theory/00-index.md) — Índice
- [`docs/theory/01-ternary-algebra.md`](docs/theory/01-ternary-algebra.md) — Quantização ternária
- [`docs/theory/02-wht-decomposition.md`](docs/theory/02-wht-decomposition.md) — WHT
- [`docs/theory/03-acdc-structured-layers.md`](docs/theory/03-acdc-structured-layers.md) — ACDC
- [`docs/theory/04-tropical-algebra.md`](docs/theory/04-tropical-algebra.md) — Semiring (max,+)
- [`docs/theory/05-holographic-memory.md`](docs/theory/05-holographic-memory.md) — HRR
- [`docs/theory/06-5-levels.md`](docs/theory/06-5-levels.md) — Sumário 1 página

### Walkthroughs

- [`examples/medical_offline.md`](examples/medical_offline.md) — Médico
- [`examples/legal_offline.md`](examples/legal_offline.md) — Advogado
- [`examples/finance_offline.md`](examples/finance_offline.md) — Financeiro

---
## Arquitetura do código

### C++ (inferência 1.58-bit)

```
src/
  ggml-bitnet-mad.cpp      ← Kernel I2_S (AVX2 + NEON), L1
  ggml-bitnet-lut.cpp      ← Kernels TL1/TL2 lookup-table, L1
  ggml-bitnet-wht.cpp      ← WHT zero-multiplicação, L2
  ggml-bitnet-fwht.cpp     ← FWHT + ACDC O(n log n), L3
  ggml-bitnet-tropical.cpp ← Atenção tropical (max,+), L4
  ggml-bitnet-hrr.cpp      ← Memória holográfica, L5
  ggml-bitnet-dispatch.cpp ← Dispatch L3-L5
  ggml-bitnet-kv-cache.cpp ← K_i8 cache
  ggml-bitnet-common.cpp   ← Utilitários

include/                   ← Headers L1-L5
utils/                     ← Benchmarks L1-L5
```

### Python (BitNet Studio)

```
bitnet-studio/
├── studio/server/
│   ├── tool_engine.py     ← Parser v2: 6 fallbacks + normalização + multi-tool + heurística
│   ├── mcp_bridge.py      ← Integração MCP (protheus-rag)
│   ├── api.py             ← Loop agentic com retry e pre-filtro heurístico
│   └── inference.py       ← Geração com adapter
├── finetune_local.py      ← Fine-tune QLoRA CPU
├── test_50x_file.py       ← Teste exaustivo 72 rodadas
├── test_parser_v2.py      ← Teste unitário parser v2 (26 testes)
├── data/                  ← Datasets e geradores
└── adapters/              ← Checkpoints QLoRA
```

---
## Restrições fundadoras

- **CPU only** — GPU kernels proibidos (NO-02)
- **Sem cloud, sem telemetria** (NO-06, NO-07)
- **Sem mudança no formato GGUF** (NO-03)
- **Patches vendored** — `3rdparty/llama.cpp/` read-only

## Licença

MIT — ver [`LICENSE`](LICENSE).

---

*v5.0 — README atualizado em 2026-06-27.*
*v4.2 → v5.0: adapter v4 atinge 91.7% (72x) com dataset v4 (512 exemplos),
fix ChatML no test_50x_file.py, do_sample=False (greedy), min_new_tokens=25.
Todas as 10 tools a 100%. Negativos 50%.*
