#!/usr/bin/env python3
"""Teste unitario do Parser v2 — normalizacao, multi-tool, confianca, retry."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from studio.server.tool_engine import (
    parse_tool_call, parse_all_tool_calls, should_use_tool,
    build_retry_prompt, _normalize_tool_name, ToolCall,
)
from studio.server.mcp_bridge import McpTool


def make_tool(qualified_name):
    server, _, name = qualified_name.partition("__")
    return McpTool(server=server, name=name, description="", input_schema={})


TOOLS = [
    make_tool("protheus-rag__consultar_base_direta"),
    make_tool("protheus-rag__consultar_dicionario_direto"),
    make_tool("protheus-rag__consultar_base_interna"),
    make_tool("protheus-rag__buscar_reversa_direto"),
    make_tool("protheus-rag__consultar_reversa_rag"),
    make_tool("protheus-rag__mem0_search"),
    make_tool("protheus-rag__mem0_add"),
    make_tool("protheus-rag__mem0_list"),
    make_tool("protheus-rag__mem0_stats"),
    make_tool("protheus-rag__mem0_delete"),
]

KNOWN = {t.qualified_name for t in TOOLS}
passed = 0
failed = 0


def check(desc, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS | {desc}")
    else:
        failed += 1
        print(f"  FAIL | {desc}")


print("=" * 60)
print("TESTE PARSER v2")
print("=" * 60)

# 1. Normalizacao de nomes
print("\n[1] Normalizacao de nomes (dashes -> underscores)")
check(
    "protheus-rag-mem0-stats -> protheus-rag__mem0_stats",
    _normalize_tool_name("protheus-rag-mem0-stats", KNOWN) == "protheus-rag__mem0_stats"
)
check(
    "protheus-rag-mem0-list -> protheus-rag__mem0_list",
    _normalize_tool_name("protheus-rag-mem0-list", KNOWN) == "protheus-rag__mem0_list"
)
check(
    "protheus-rag-mem0-search -> protheus-rag__mem0_search",
    _normalize_tool_name("protheus-rag-mem0-search", KNOWN) == "protheus-rag__mem0_search"
)
check(
    "nome correto passa direto",
    _normalize_tool_name("protheus-rag__mem0_list", KNOWN) == "protheus-rag__mem0_list"
)
check(
    "nome inexistente retorna None",
    _normalize_tool_name("ferramenta-inexistente", KNOWN) is None
)

# 2. Parser com nome normalizado
print("\n[2] Parser com nome dash normalizado")
resp_dash = '<tool_call>\nprotheus-rag-mem0-stats\n</tool_call>'
tc = parse_tool_call(resp_dash, TOOLS)
check("parse_tool_call normaliza dash sem JSON", tc is not None and tc.name == "protheus-rag__mem0_stats")

resp_dash2 = '<tool_call>\n{"name": "protheus-rag-mem0-list", "arguments": {}}\n</tool_call>'
tc2 = parse_tool_call(resp_dash2, TOOLS)
check("parse_tool_call normaliza dash com JSON", tc2 is not None and tc2.name == "protheus-rag__mem0_list")

# 3. Multi-tool
print("\n[3] Multi-tool (parse_all_tool_calls)")
multi = (
    '<tool_call>\n{"name": "protheus-rag__mem0_search", "arguments": {"query": "teste"}}\n</tool_call>\n'
    '\n'
    '<tool_call>\n{"name": "protheus-rag__mem0_list", "arguments": {}}\n</tool_call>\n'
)
calls = parse_all_tool_calls(multi, TOOLS)
check("extrai 2 tool calls", len(calls) == 2)
check("primeira e mem0_search", calls[0].name == "protheus-rag__mem0_search")
check("segunda e mem0_list", calls[1].name == "protheus-rag__mem0_list")

# Dedup
multi_dup = (
    '<tool_call>\n{"name": "protheus-rag__mem0_search", "arguments": {"query": "a"}}\n</tool_call>\n'
    '\n'
    '<tool_call>\n{"name": "protheus-rag__mem0_search", "arguments": {"query": "b"}}\n</tool_call>\n'
)
calls_dup = parse_all_tool_calls(multi_dup, TOOLS)
check("deduplica mesma tool", len(calls_dup) == 1)

# 4. should_use_tool (heuristica de confianca)
print("\n[4] should_use_tool (heuristica)")
check(
    "'Liste todas as memorias' -> mem0_list",
    should_use_tool("Liste todas as memórias salvas", TOOLS) == "protheus-rag__mem0_list"
)
check(
    "'Quantas memorias temos?' -> mem0_stats",
    should_use_tool("Quantas memórias temos na base?", TOOLS) == "protheus-rag__mem0_stats"
)
check(
    "'Anote que o cliente...' -> mem0_add",
    should_use_tool("Anote que o cliente prefere e-mail", TOOLS) == "protheus-rag__mem0_add"
)
check(
    "'O que sabemos sobre...' -> mem0_search",
    should_use_tool("O que sabemos sobre o cliente João?", TOOLS) == "protheus-rag__mem0_search"
)
check(
    "'Quais campos tem a tabela SA1?' -> dicionario",
    should_use_tool("Quais campos tem a tabela SA1?", TOOLS) == "protheus-rag__consultar_dicionario_direto"
)
check(
    "'Como funciona a funcao MaFisCalc?' -> base_direta",
    should_use_tool("Como funciona a função MaFisCalc?", TOOLS) == "protheus-rag__consultar_base_direta"
)
check(
    "'Olá, como vai?' -> None",
    should_use_tool("Olá, como vai?", TOOLS) is None
)
check(
    "'Quanto é 2 + 2?' -> None",
    should_use_tool("Quanto é 2 + 2?", TOOLS) is None
)
check(
    "'Bom dia!' -> None",
    should_use_tool("Bom dia!", TOOLS) is None
)
check(
    "'Como criar um REST endpoint em TLPP?' -> reversa_rag",
    should_use_tool("Como criar um REST endpoint em TLPP?", TOOLS) == "protheus-rag__consultar_reversa_rag"
)

# 5. build_retry_prompt
print("\n[5] build_retry_prompt")
retry = build_retry_prompt("resposta malformada", TOOLS)
check("retry contem nome exato", "protheus-rag__mem0_list" in retry)
check("retry contem formato", '"name"' in retry and '"arguments"' in retry)

# 6. Casos edge do parser
print("\n[6] Casos edge")
check(
    "texto vazio -> None",
    parse_tool_call("", TOOLS) is None
)
check(
    "texto sem tool call -> None",
    parse_tool_call("Resposta direta sem ferramenta.", TOOLS) is None
)
check(
    "JSON puro sem tag -> funciona",
    parse_tool_call('{"name": "protheus-rag__mem0_list", "arguments": {}}', TOOLS) is not None
)

# Resultado final
print(f"\n{'='*60}")
print(f"RESULTADO: {passed} pass, {failed} fail, {passed+failed} total")
print(f"Taxa: {passed/(passed+failed)*100:.1f}%")
print(f"{'='*60}")
