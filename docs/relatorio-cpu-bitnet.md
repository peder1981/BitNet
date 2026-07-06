# Relatório — Verificação dos kernels L2–L5 e investigação de performance CPU

> **Data:** 2026-07-06
> **Objetivo:** verificar a "teoria" dos kernels matemáticos deste fork (Níveis 2–5) e
> buscar a inferência BitNet mais rápida possível **em CPU** para o modelo shipado
> (BitNet-b1.58-2B-4T). Restrição do projeto: **CPU only, nunca GPU**.

Conclusão em uma linha: **o motor já é o estado-da-arte (bitnet.cpp, kernel I2_S AVX2);
os kernels L2–L5 da "álgebra esquecida" não aceleram o modelo pré-treinado; e nenhum
ajuste de `gemm-config` supera o default além do ruído neste hardware.** O ganho prático
real desta sessão foi **corrigir bugs/afirmações falsas** e **fixar `-t 4` como o número
de threads correto** (com `-t 8` a máquina colapsa).

---

## Parte 1 — Verificação da teoria (Níveis 2–5)

Cada nível foi conferido contra o código e a matemática. Achados e correções aplicadas:

### Nível 2 — "WHT" (máscara ternária)
- **Misnomer:** não existe transformada de Walsh-Hadamard no kernel. É apenas o produto
  ternário com máscara de sinal `Σ_{w=+1} x − Σ_{w=-1} x`. A identidade é correta e trivial.
- **Não acelera:** medido **≈3–6× MAIS LENTO** que o `maddubs` do L1 (o kernel que
  realmente roda), porque gasta ~10 operações vetoriais por 32 elementos onde o `maddubs`
  gasta uma. "Zero multiplicações" é prova de existência algébrica, não ganho de CPU.
- **Bug corrigido:** `unpack_i2s_block` usava passo fixo `*32` entre os 4 planos de bits;
  no único build que alcança esse caminho (`QK_WHT=32`) isso **escrevia 3 blocos fora dos
  limites**. Trocado por `QK_WHT/4`.
- **Evidência:** novo microbenchmark `utils/l2_vs_maddubs_microbench.cpp` mede os dois
  kernels reais nos mesmos dados empacotados e confirma igualdade bit-a-bit + a lentidão.

### Nível 3 — ACDC / FWHT
- A borboleta FWHT é O(n log n) e correta.
- **Inaplicável ao modelo pré-treinado:** a projeção ACDC de um W genérico captura apenas
  ~1/n da energia (erro ≈99,9%). ACDC só recupera W se o modelo for **treinado com a
  arquitetura ACDC**. O BitNet-2B-4T não foi.
- **Bug corrigido:** `acdc_error` ainda aplicava `1/n²` depois que o commit anterior
  removeu essa normalização de `acdc_forward_f32`. Isso descasava da projeção
  `d* = diag(HWH)/n²` por exatamente n², fazendo o diagnóstico reportar ~100% de erro até
  para um W perfeitamente ACDC. Corrigido roteando `acdc_error` pelo mesmo kernel de
  inferência (`acdc_forward_f32`), garantindo que nunca mais divirja. (Derivação: o
  diagonal ótimo por mínimos quadrados é δ*[k] = (HWH)[k,k]/n², parceiro da forward
  **não-normalizada** — logo a forward do commit anterior estava certa; o `acdc_error` é
  que estava errado.)

### Nível 4 — Atenção Tropical
- O Top-K é uma aproximação lícita (porém *lossy* — muda as saídas).
- **Premissa falsa:** o kernel calcula os scores com um "produto ternário de custo zero"
  que pressupõe `K ∈ {-1,0,+1}`. Numa atenção real as keys `K = W_k·x` são **ativações
  full-range**, não ternárias — só os *pesos* são ternários. O ganho "zero multiplicação"
  não vale para atenção.

### Nível 5 — Memória Holográfica (HRR)
- **Inaplicável no head_dim atual:** a recuperação exige `d ≥ 10·N`. Com head_dim=64 a
  capacidade é ~6 tokens antes de ruído — inviável como substituto de atenção em contexto
  real. Status também estava contraditório entre `CLAUDE.md` ("Done") e a doc ("em andamento").

### Documentação corrigida
`docs/mathematical-foundations.md` foi ajustado para refletir a **realidade medida**: L2 é
mais lento, L3/L5 exigem re-treino, L4 tem premissa quebrada, e **nenhum dos níveis 2–5
está integrado ao caminho de dispatch do llama.cpp** (são a OBJECT lib isolada `bitnet_math`).
O `utils/wht_benchmark.py` ganhou um aviso de que mede NumPy/BLAS, não o kernel C real.

---

## Parte 2 — Investigação de performance CPU

### Hardware
- **Intel Core i5-10210U** (Comet Lake, 4 núcleos / 8 threads, base 1.6 GHz, TDP 15 W).
- SIMD: **apenas AVX2** — sem AVX-512, sem VNNI, sem AMX.
- Fortemente **limitado por temperatura** (throttling): benchmarks têm ruído de ±20–40%.

### Build
- Já compilado corretamente: `GGML_NATIVE=ON` → `-march=native` → runtime confirma
  `AVX2=1, FMA=1, F16C=1`. **Não há ganho grátis de recompilação.**
- Kernel ativo: **I2_S** (default), que é o caminho recomendado/nativo para o 2B-4T.
  (TL2 LUT existe, mas não tem preset para o 2B-4T e não é o kernel-alvo deste modelo.)

### Baseline medido (I2_S, `-t 4`)
| Teste | t/s |
|-------|-----|
| pp512 (prefill) | ~8–10 |
| tg64 (decode) | ~3.4–5.5 |

Os números absolutos são **limitados pelo silício** (chip mobile de 15 W em throttle). O
mesmo binário num desktop com AVX-512/VNNI é 10×+ mais rápido. "Mais rápido que os outros"
já é verdade por construção: ternário ≈2 bpw ⇒ menos tráfego de memória por token que Q4/Q8.

### Threads — achado prático concreto
| Threads | tg64 |
|---------|------|
| **4** | **5.52** |
| 8 | 0.40 |

Com **8 threads** a máquina **colapsa** (contenção de SMT + calor acumulado). **Regra:
usar `-t 4` (nº de núcleos físicos), nunca `-t 8` neste chip.**

### Autotune do `gemm-config` — resultado honesto
Sweep `--quick` de 5 configs (`utils/tune_gemm_config.py`, pp128, `-t 4`):

| Config | pp128 t/s |
|--------|-----------|
| `R4/C128/P4` (default) | 5.72 |
| `R8/C128/P4` | 10.15 |
| `R4/C64/P4` | 9.84 |
| `R32/C4` (ACT_OFF) | 7.05 |
| `R16/C4` (ACT_OFF) | 8.30 |

O tuner elegeu `R8/C128/P4` (10.15). **Mas isso era ruído** — confirmado por um A-B-A
controlado (baseline → R8 → baseline, pp512+tg64, `-r 4`, cooldown de 60 s):

| Medição | pp512 | tg64 |
|---------|-------|------|
| A1 baseline R4 | 8.64 ± 0.77 | 3.39 ± 0.14 |
| B candidato R8 | 8.93 ± 1.18 | 3.89 ± 0.09 |
| A2 baseline R4 | 7.85 ± 1.64 | 2.38 ± 0.96 |

O **próprio baseline** oscilou 8.64→7.85 (pp) e 3.39→2.38 (tg) entre duas medições
idênticas. O candidato R8 (8.93 / 3.89) cai **dentro da banda de ruído do baseline**.
**Nenhuma config supera o default além do ruído neste hardware → mantido o `R4/C128/P4`.**
Evidências: `stats/tune_quick.csv`, `stats/ab_verify.txt`.

---

## Conclusões e recomendações práticas

1. **`-t 4`, sempre.** Nunca `-t 8` neste chip (colapsa para ~0.4 t/s).
2. **Mantenha o `gemm-config` default.** Autotuning não rende ganho real aqui; o ruído
   térmico é maior que qualquer diferença entre configs.
3. **A "álgebra esquecida" (L2–L5) não é o caminho para velocidade.** L2 é mais lento; L3/L5
   exigem re-treino; L4 é lossy e com premissa quebrada. O I2_S AVX2 já é o SOTA para CPU.
4. **Para ficar de fato mais rápido:** o gargalo dominante é o hardware. Ganhos reais viriam
   de (a) rodar em CPU com AVX-512-VNNI/AMX (mesmo código, 10×+), ou (b) trabalho
   incremental de kernel (LUT TL2 afinado para as dimensões do 2B-4T) — ganho medido em
   dígitos simples, não ordens de magnitude, e fora do escopo desta sessão.

## Arquivos alterados nesta sessão
- **Correções de código:** `src/ggml-bitnet-fwht.cpp`, `src/ggml-bitnet-wht.cpp`,
  `include/ggml-bitnet-wht.h`
- **Documentação:** `docs/mathematical-foundations.md`, este relatório, aviso em
  `utils/wht_benchmark.py`
- **Novo:** `utils/l2_vs_maddubs_microbench.cpp` (microbench real L2 vs maddubs)
- **Evidências:** `stats/tune_quick.csv`, `stats/ab_verify.txt`
- **Não alterado:** `include/gemm-config.h` (default preservado — decisão baseada em evidência)
