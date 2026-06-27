"""Teste rapido e eficiente do adapter v3 — 12 perguntas, 1 iteracao, ~30min."""
import json, sys, time
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, str(Path(__file__).parent))
from studio.server.tool_engine import parse_tool_call

BASE = "tiiuae/Falcon3-3B-Instruct"
ADAPTER = "adapters/f3b-ptbr-tools-v3"

torch.set_num_threads(4)

class MockTool:
    def __init__(self, name):
        self.qualified_name = name
        self.description = ""
        self.input_schema = {}

TOOLS = [
    MockTool("protheus-rag__consultar_base_direta"),
    MockTool("protheus-rag__consultar_dicionario_direto"),
    MockTool("protheus-rag__consultar_base_interna"),
    MockTool("protheus-rag__buscar_reversa_direto"),
    MockTool("protheus-rag__consultar_reversa_rag"),
    MockTool("protheus-rag__mem0_search"),
    MockTool("protheus-rag__mem0_add"),
    MockTool("protheus-rag__mem0_list"),
    MockTool("protheus-rag__mem0_stats"),
    MockTool("protheus-rag__mem0_delete"),
]

QUESTIONS = [
    ("Como funciona a funcao MaFisCalc?", "protheus-rag__consultar_base_direta"),
    ("Quais campos tem a tabela SA1?", "protheus-rag__consultar_dicionario_direto"),
    ("Como funciona o faturamento no Protheus?", "protheus-rag__consultar_base_interna"),
    ("Como usar o skill reversa-scout?", "protheus-rag__buscar_reversa_direto"),
    ("Como criar um REST endpoint em TLPP?", "protheus-rag__consultar_reversa_rag"),
    ("O que sabemos sobre o cliente Joao Silva?", "protheus-rag__mem0_search"),
    ("Anote que o cliente prefere contato por e-mail", "protheus-rag__mem0_add"),
    ("Liste todas as memorias salvas", "protheus-rag__mem0_list"),
    ("Quantas memorias temos na base?", "protheus-rag__mem0_stats"),
    ("Apague a memoria sobre o teste", "protheus-rag__mem0_delete"),
    ("Ola, como vai?", None),
    ("Quanto e 2 + 2?", None),
]

print("Carregando modelo...", flush=True)
tok = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True, use_fast=False, clean_up_tokenization_spaces=False)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

model = AutoModelForCausalLM.from_pretrained(BASE, torch_dtype=torch.float32, device_map="cpu", trust_remote_code=True)
model = PeftModel.from_pretrained(model, ADAPTER)
model.eval()
print("Modelo carregado!\n", flush=True)

def generate(prompt, max_tokens=128):
    inputs = tok(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            min_new_tokens=25,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tok.pad_token_id,
            eos_token_id=tok.eos_token_id,
        )
    text = tok.decode(outputs[0], skip_special_tokens=False)
    if "<|im_start|>assistant" in text:
        text = text.split("<|im_start|>assistant")[-1].strip()
    return text

passed = 0
failed = 0
results = []

for q_text, expected_tool in QUESTIONS:
    prompt = f"<|im_start|>user\n{q_text}\n<|im_end|>\n<|im_start|>assistant\n"
    t0 = time.time()
    response = generate(prompt)
    elapsed = time.time() - t0

    tc = parse_tool_call(response, TOOLS)
    got_tool = tc.name if tc else None
    ok = got_tool == expected_tool
    status = "PASS" if ok else "FAIL"
    if ok:
        passed += 1
    else:
        failed += 1

    print(f"{status} | {q_text[:35]:35} | exp={str(expected_tool):40} | got={str(got_tool):40} | {elapsed:.1f}s", flush=True)
    if not ok:
        print(f"  Response: {response[:200]}", flush=True)

    results.append({
        "question": q_text,
        "expected": expected_tool,
        "got": got_tool,
        "pass": ok,
        "elapsed": round(elapsed, 2),
        "response": response[:300],
    })

print(f"\n{'='*60}")
print(f"RESULTADO: {passed}/{passed+failed} ({passed/(passed+failed)*100:.1f}%)")
print(f"{'='*60}")

with open("test_quick_results.json", "w", encoding="utf-8") as f:
    json.dump({"total": passed+failed, "passed": passed, "failed": failed,
               "accuracy": passed/(passed+failed), "results": results}, f, ensure_ascii=False, indent=2)
print("Salvo em test_quick_results.json")
