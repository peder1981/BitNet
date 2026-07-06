/*
 * l2_vs_maddubs_microbench.cpp
 *
 * Measures the real L2 "WHT" ternary-mask dot (ggml_wht_raw_dot) against the
 * production I2_S maddubs dot on IDENTICAL packed data. Purpose: substantiate,
 * with a number instead of a header comment, that L2 is NOT faster than the
 * maddubs kernel it claims to beat.
 *
 * It also asserts the two agree bit-exactly with a scalar reference
 *   Σ w·x  ==  maddubs(Σ e·x) − Σ x        (e = w+1 ∈ {0,1,2})
 * which doubles as the correctness check ponytail requires for SIMD logic.
 *
 * Build (x86_64, AVX2):
 *   clang++ -O3 -mavx2 -std=c++17 utils/l2_vs_maddubs_microbench.cpp \
 *           src/ggml-bitnet-wht.cpp -Iinclude -o /tmp/l2bench && /tmp/l2bench
 *
 * ponytail: AVX2-only microbench; on non-AVX2 hardware it prints a skip and
 *           exits 0 (the claim it checks is an AVX2 claim).
 */
#include "ggml-bitnet-wht.h"
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <cassert>
#include <chrono>
#include <random>
#include <vector>

#if !defined(__AVX2__)
int main() { printf("[skip] built without AVX2 — the L2-vs-maddubs claim is AVX2-only\n"); return 0; }
#else
#include <immintrin.h>

static constexpr int QK = 128;   /* I2_S x86 block size */

/* Faithful copy of the I2_S maddubs inner loop (see ggml-bitnet-mad.cpp:226).
 * Returns Σ e·x with e = packed 2-bit value ∈ {0,1,2}; caller subtracts Σx. */
static int32_t maddubs_dot(int n, const uint8_t *packed, const int8_t *x) {
    const int nb = n / QK;
    const __m256i mask  = _mm256_set1_epi8(0x03);
    const __m256i one16 = _mm256_set1_epi16(1);
    __m256i accu = _mm256_setzero_si256();
    for (int b = 0; b < nb; b++) {
        const uint8_t *px = packed + b * 32;
        const int8_t  *py = x + b * QK;
        __m256i p  = _mm256_loadu_si256((const __m256i*)px);
        __m256i g0 = _mm256_and_si256(_mm256_srli_epi16(p, 6), mask);
        __m256i g1 = _mm256_and_si256(_mm256_srli_epi16(p, 4), mask);
        __m256i g2 = _mm256_and_si256(_mm256_srli_epi16(p, 2), mask);
        __m256i g3 = _mm256_and_si256(p, mask);
        __m256i y0 = _mm256_loadu_si256((const __m256i*)(py));
        __m256i y1 = _mm256_loadu_si256((const __m256i*)(py + 32));
        __m256i y2 = _mm256_loadu_si256((const __m256i*)(py + 64));
        __m256i y3 = _mm256_loadu_si256((const __m256i*)(py + 96));
        __m256i s = _mm256_add_epi16(
            _mm256_add_epi16(_mm256_maddubs_epi16(g0, y0), _mm256_maddubs_epi16(g1, y1)),
            _mm256_add_epi16(_mm256_maddubs_epi16(g2, y2), _mm256_maddubs_epi16(g3, y3)));
        accu = _mm256_add_epi32(accu, _mm256_madd_epi16(s, one16));
    }
    __m128i lo = _mm256_castsi256_si128(accu);
    __m128i hi = _mm256_extracti128_si256(accu, 1);
    __m128i sum = _mm_add_epi32(lo, hi);
    sum = _mm_hadd_epi32(sum, sum);
    sum = _mm_hadd_epi32(sum, sum);
    return _mm_cvtsi128_si32(sum);
}

static int32_t sum_i8(int n, const int8_t *x) {
    int32_t s = 0; for (int i = 0; i < n; i++) s += x[i]; return s;
}

/* Pack ternary weights into the I2_S layout both kernels expect:
 * bits[7:6]→positions 0..31, [5:4]→32..63, [3:2]→64..95, [1:0]→96..127. */
static void pack_ternary(int n, const int8_t *w, uint8_t *packed) {
    const int nb = n / QK;
    memset(packed, 0, (size_t)n / 4);
    for (int b = 0; b < nb; b++) {
        uint8_t *dst = packed + b * 32;
        const int8_t *wb = w + b * QK;
        for (int pos = 0; pos < QK; pos++) {
            int g = pos / 32, col = pos % 32;
            uint8_t e = (uint8_t)(wb[pos] + 1);      /* {-1,0,1} -> {0,1,2} */
            dst[col] |= (uint8_t)(e << (6 - 2 * g));
        }
    }
}

int main() {
    const int n = 2560;          /* BitNet-2B FFN dim, multiple of 128 */
    const int iters = 200000;
    std::mt19937 rng(42);
    std::vector<int8_t> w(n), x(n);
    std::uniform_int_distribution<int> tern(0, 999), act(-127, 127);
    for (int i = 0; i < n; i++) {
        int r = tern(rng);                            /* ~45% zeros, like BitNet */
        w[i] = (r < 275) ? -1 : (r < 550 ? 1 : 0);
        x[i] = (int8_t)act(rng);
    }
    std::vector<uint8_t> packed((size_t)n / 4);
    pack_ternary(n, w.data(), packed.data());

    /* correctness: both paths must equal the scalar reference */
    int64_t ref = 0;
    for (int i = 0; i < n; i++) ref += (int)w[i] * (int)x[i];
    int32_t r_l2  = ggml_wht_raw_dot(n, packed.data(), x.data());
    int32_t r_mad = maddubs_dot(n, packed.data(), x.data()) - sum_i8(n, x.data());
    printf("correctness: ref=%lld  L2=%d  maddubs=%d\n", (long long)ref, r_l2, r_mad);
    assert(r_l2 == (int32_t)ref && r_mad == (int32_t)ref);

    /* timing — separate loops, volatile sink defeats dead-code elimination.
     * The maddubs −Σx correction is per-token (amortized over all rows), so it
     * is fairly excluded from the per-dot cost. */
    volatile int32_t sink = 0;
    auto t0 = std::chrono::high_resolution_clock::now();
    for (int k = 0; k < iters; k++) sink += ggml_wht_raw_dot(n, packed.data(), x.data());
    auto t1 = std::chrono::high_resolution_clock::now();
    for (int k = 0; k < iters; k++) sink += maddubs_dot(n, packed.data(), x.data());
    auto t2 = std::chrono::high_resolution_clock::now();
    (void)sink;

    double l2_ns  = std::chrono::duration<double, std::nano>(t1 - t0).count() / iters;
    double mad_ns = std::chrono::duration<double, std::nano>(t2 - t1).count() / iters;
    printf("n=%d  iters=%d\n", n, iters);
    printf("  L2  (ggml_wht_raw_dot, mask+sub) : %8.1f ns/dot\n", l2_ns);
    printf("  MAD (maddubs)                    : %8.1f ns/dot\n", mad_ns);
    printf("  => L2 is %.2fx %s than maddubs\n",
           l2_ns > mad_ns ? l2_ns / mad_ns : mad_ns / l2_ns,
           l2_ns > mad_ns ? "SLOWER" : "faster");
    return 0;
}
#endif
