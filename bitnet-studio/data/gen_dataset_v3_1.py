#!/usr/bin/env python3
"""Gera dataset v3.1 — focado nos 4 problemas do v3:

1. mem0_list/mem0_stats: modelo gera tag mas nao completa JSON
   -> 30 exemplos extras com JSON completo e arguments vazios {}
2. mem0_add: confundido com mem0_search
   -> 20 exemplos contrastivos (mesmo contexto, tool diferente)
3. consultar_reversa_rag: confundido com consultar_base_interna
   -> 20 exemplos contrastivos
4. Nome da tool com dashes vs underscores
   -> Garantir que todos os exemplos usam protheus-rag__tool_name
"""
import json
import random

random.seed(42)

# ========== EXEMPLOS PARA mem0_list (JSON completo com arguments vazios) ==========

mem0_list_questions = [
    "Liste todas as memórias salvas",
    "Liste todas as memórias",
    "Me mostre as memórias",
    "Quais memórias temos salvas?",
    "Mostre a lista de memórias",
    "Liste as memórias do sistema",
    "Quais são as memórias armazenadas?",
    "Liste tudo que foi anotado",
    "Me mostre tudo que temos salvo",
    "Liste as anotações",
    "Quais anotações temos?",
    "Mostre todas as memórias",
    "Liste as memórias persistidas",
    "Quais são as memórias da base?",
    "Liste o conteúdo da memória",
    "Pode listar as memórias?",
    "Ver todas as memórias",
    "Quero ver as memórias salvas",
    "Tem alguma memória salva?",
    "Liste as memórias existentes",
    "Mostre as memórias do sistema",
    "Quais memórias estão armazenadas?",
    "Liste as memórias registradas",
    "Verifique as memórias salvas",
    "Liste as memórias do banco",
    "Mostre a lista de anotações",
    "Quais são as anotações salvas?",
    "Liste as memórias disponíveis",
    "Tem memórias? Liste todas",
    "Verifique o conteúdo da memória",
]

mem0_list_results = [
    "Temos 20 memórias armazenadas.",
    "A base contém 15 memórias.",
    "Existem 25 memórias salvas no sistema.",
    "Atualmente temos 18 memórias.",
    "A lista de memórias contém 22 registros.",
]

def make_mem0_list(question, result_idx):
    result = mem0_list_results[result_idx % len(mem0_list_results)]
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": '{"name": "protheus-rag__mem0_list", "arguments": {}}\n'},
            {"role": "user", "content": "Resultado da ferramenta `protheus-rag__mem0_list`:\n```\nTotal: 20 memórias\n// Lista\n...\n\n```\nUse esse resultado para responder ao usuário em português."},
            {"role": "assistant", "content": result},
        ]
    }


# ========== EXEMPLOS PARA mem0_stats (JSON completo com arguments vazios) ==========

mem0_stats_questions = [
    "Quantas memórias temos na base?",
    "Quantas memórias temos?",
    "Qual o total de memórias?",
    "Estatísticas das memórias",
    "Estatísticas da base de memórias",
    "Quantas anotações temos?",
    "Qual o número de memórias salvas?",
    "Me dê as estatísticas de memória",
    "Quantos registros temos na memória?",
    "Estatísticas gerais das memórias",
    "Qual o tamanho da base de memórias?",
    "Quantas memórias existem?",
    "Me mostre as estatísticas da memória",
    "Qual a quantidade de memórias?",
    "Resumo estatístico das memórias",
    "Quantas memórias estão cadastradas?",
    "Estatísticas da memória",
    "Total de memórias no sistema",
    "Quantas entradas temos na memória?",
    "Estatísticas completas das memórias",
    "Qual o número total de memórias?",
    "Me mostre as estatísticas",
    "Quantas memórias foram salvas?",
    "Estatísticas atuais das memórias",
    "Qual o tamanho da memória?",
    "Quantos itens temos na memória?",
    "Resumo das memórias",
    "Estatísticas do banco de memórias",
    "Quantas memórias há na base?",
    "Me dê um resumo estatístico",
]

mem0_stats_results = [
    "A base contém 20 memórias.",
    "Temos 18 memórias no total.",
    "O sistema possui 25 memórias cadastradas.",
    "Atualmente há 15 memórias armazenadas.",
    "O total de memórias é 22.",
]

def make_mem0_stats(question, result_idx):
    result = mem0_stats_results[result_idx % len(mem0_stats_results)]
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": '{"name": "protheus-rag__mem0_stats", "arguments": {}}\n'},
            {"role": "user", "content": "Resultado da ferramenta `protheus-rag__mem0_stats`:\n```\nTotal: 20 memórias\nCategorias: fact, preference, context\n...\n\n```\nUse esse resultado para responder ao usuário em português."},
            {"role": "assistant", "content": result},
        ]
    }


# ========== EXEMPLOS CONTRASTIVOS: mem0_add vs mem0_search ==========

# mem0_add: "anote/salve/registre" -> acao de guardar
mem0_add_extra = [
    ("Anote que o cliente prefere contato por e-mail", "cliente prefere contato por e-mail"),
    ("Salve que o cliente João paga em 30 dias", "cliente João paga em 30 dias"),
    ("Anote que a versão do Protheus é 12.1.33", "versão do Protheus é 12.1.33"),
    ("Salve que o servidor é Linux Ubuntu 22.04", "servidor é Linux Ubuntu 22.04"),
    ("Anote que o banco de dados é SQL Server", "banco de dados é SQL Server"),
    ("Salve que o cliente trabalha com o ramo varejo", "cliente trabalha com ramo varejo"),
    ("Anote que o fuso horário é UTC-3", "fuso horário é UTC-3"),
    ("Salve que o idioma padrão é português", "idioma padrão é português"),
    ("Anote que o cliente tem 50 usuários", "cliente tem 50 usuários"),
    ("Salve que a empresa usa TOTVS Protheus", "empresa usa TOTVS Protheus"),
    ("Anote que o responsável técnico é Carlos", "responsável técnico é Carlos"),
    ("Salve que o prazo de entrega é 15 dias úteis", "prazo de entrega é 15 dias úteis"),
    ("Anote que o cliente quer relatório mensal", "cliente quer relatório mensal"),
    ("Salve que o orçamento do projeto é R$ 50 mil", "orçamento do projeto é R$ 50 mil"),
    ("Registre que o cliente está ativo desde 2020", "cliente está ativo desde 2020"),
    ("Anote que a filial principal é em São Paulo", "filial principal é em São Paulo"),
    ("Salve que o contrato foi renovado em janeiro", "contrato foi renovado em janeiro"),
    ("Anote que o cliente precisa de suporte prioritário", "cliente precisa de suporte prioritário"),
    ("Registre que o pagamento é via boleto", "pagamento é via boleto"),
    ("Salve que o contato do cliente é carlos@empresa.com", "contato do cliente é carlos@empresa.com"),
]

def make_mem0_add(question, content_text):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'{{"name": "protheus-rag__mem0_add", "arguments": {{"content": "{content_text}"}}}}\n'},
            {"role": "user", "content": "Resultado da ferramenta `protheus-rag__mem0_add`:\n```\nMemória adicionada com sucesso.\n```\nUse esse resultado para responder ao usuário em português."},
            {"role": "assistant", "content": "Anotado com sucesso."},
        ]
    }


# mem0_search: "o que sabemos/buscar/recuperar" -> acao de consultar
mem0_search_extra = [
    "O que sabemos sobre o cliente João Silva?",
    "O que sabemos sobre o cliente Maria Santos?",
    "O que sabemos sobre o fornecedor ABC Ltda?",
    "Quais são as preferências do cliente?",
    "O que foi decidido sobre o projeto X?",
    "Buscar memórias sobre o módulo faturamento",
    "O que sabemos sobre o usuário admin?",
    "O que temos anotado sobre o cliente empresa XYZ?",
    "Recupere informações sobre o contrato 123",
    "O que sabemos sobre o fornecedor Tech Corp?",
    "Buscar contexto sobre a reunião de ontem",
    "O que lembramos sobre o bug do faturamento?",
    "O que temos sobre o cliente Pedro?",
    "Recupere as anotações sobre o projeto Alpha",
    "O que sabemos da empresa Beta Ltda?",
    "Buscar informações sobre o contrato 456",
    "O que foi anotado sobre o servidor?",
    "Recupere memórias sobre o módulo compras",
    "O que sabemos sobre o prazo de entrega?",
    "Buscar contexto sobre o orçamento do projeto",
]

def make_mem0_search(question):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'{{"name": "protheus-rag__mem0_search", "arguments": {{"query": "{question}"}}}}\n'},
            {"role": "user", "content": "Resultado da ferramenta `protheus-rag__mem0_search`:\n```\n[1] (score 0.85)\nMemória encontrada com contexto relevante.\n\n```\nUse esse resultado para responder ao usuário em português."},
            {"role": "assistant", "content": "Encontrei informações relevantes na memória."},
        ]
    }


# ========== EXEMPLOS CONTRASTIVOS: consultar_reversa_rag vs consultar_base_interna ==========

# consultar_reversa_rag: "como criar/fazer/usar" algo do framework Reversa
reversa_rag_extra = [
    "Como criar um REST endpoint em TLPP?",
    "Como gerar código MVC no Protheus?",
    "Como criar um ponto de entrada?",
    "Como documentar função AdvPL?",
    "Como migrar AdvPL para TLPP?",
    "Como criar endpoint REST com annotations?",
    "Como usar oRest object em TLPP?",
    "Como gerar ProtheusDOC?",
    "Como criar uma User Function?",
    "Como usar FWRest client?",
    "Como implementar try-catch em TLPP?",
    "Como usar named parameters em TLPP?",
    "Como criar classe com access modifiers em TLPP?",
    "Como usar JSON inline em TLPP?",
    "Como remover StaticCall migrando para TLPP?",
    "Como usar namespaces em TLPP?",
    "Como adicionar tipagem em TLPP?",
    "Como criar endpoint @Get em TLPP?",
    "Como criar endpoint @Post em TLPP?",
    "Como usar TTALK no Protheus?",
]

def make_reversa_rag(question):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'{{"name": "protheus-rag__consultar_reversa_rag", "arguments": {{"pergunta": "{question}"}}}}\n'},
            {"role": "user", "content": f"Resultado da ferramenta `protheus-rag__consultar_reversa_rag`:\n```\n[1] Reversa (score 0.86)\n// Resposta interpretada\n{question} envolve...\n\n```\nUse esse resultado para responder ao usuário em português."},
            {"role": "assistant", "content": "Para isso, use os recursos do framework Reversa conforme documentação."},
        ]
    }


# consultar_base_interna: "como funciona/explicar" processo de negocio
base_interna_extra = [
    "Como funciona o faturamento no Protheus?",
    "Explique o processo de contabilização",
    "Como funciona a rotina de compras?",
    "Me explique o ciclo financeiro do Protheus",
    "Como funciona o estoque no Protheus?",
    "Explique o módulo de faturamento",
    "Como funciona a contabilidade no Protheus?",
    "Me explique o processo de recebimento",
    "Como funciona a rotina de vendas?",
    "Explique o fluxo de caixa no Protheus",
    "Como funciona o módulo de ativos?",
    "Me explique o processo de importação",
    "Como funciona a conciliação bancária?",
    "Explique o processo de exportação",
    "Como funciona o orçamento no Protheus?",
    "Me explique a rotina de inventário",
    "Como funciona o ponto de entrada no Protheus?",
    "Explique o processo de devolução",
    "Como funciona a apuração de impostos?",
    "Me explique o módulo de recursos humanos",
]

def make_base_interna(question):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'{{"name": "protheus-rag__consultar_base_interna", "arguments": {{"pergunta": "{question}"}}}}\n'},
            {"role": "user", "content": f"Resultado da ferramenta `protheus-rag__consultar_base_interna`:\n```\n[1] Documentação (score 0.82)\n// Resposta interpretada\nO processo envolve várias etapas...\n\n```\nUse esse resultado para responder ao usuário em português."},
            {"role": "assistant", "content": "O processo funciona através de etapas integradas no Protheus."},
        ]
    }


# ========== GERAR DATASET ==========

# 1. Carregar v3
with open("data/ptbr_tools_train_v3.jsonl", encoding="utf-8") as f:
    v3 = [json.loads(line) for line in f if line.strip()]

print(f"Dataset v3: {len(v3)} exemplos")

# 2. Gerar extras
extras = []

# mem0_list: 30 exemplos
for i, q in enumerate(mem0_list_questions):
    extras.append(make_mem0_list(q, i))

# mem0_stats: 30 exemplos
for i, q in enumerate(mem0_stats_questions):
    extras.append(make_mem0_stats(q, i))

# mem0_add: 20 exemplos
for q, content in mem0_add_extra:
    extras.append(make_mem0_add(q, content))

# mem0_search: 20 exemplos
for q in mem0_search_extra:
    extras.append(make_mem0_search(q))

# consultar_reversa_rag: 20 exemplos
for q in reversa_rag_extra:
    extras.append(make_reversa_rag(q))

# consultar_base_interna: 20 exemplos
for q in base_interna_extra:
    extras.append(make_base_interna(q))

print(f"Extras v3.1: {len(extras)} exemplos")

# 3. Combinar e embaralhar
combined = v3 + extras
random.shuffle(combined)

# 4. Salvar
with open("data/ptbr_tools_train_v3_1.jsonl", "w", encoding="utf-8") as f:
    for ex in combined:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"\nTotal dataset v3.1: {len(combined)} exemplos")

# Estatisticas
from collections import Counter
import re
tool_counts = Counter()
neg_count = 0
for ex in combined:
    msgs = ex["messages"]
    assistant_msg = msgs[1]["content"] if len(msgs) > 1 else ""
    if '"name"' in assistant_msg:
        m = re.search(r'"name":\s*"([^"]+)"', assistant_msg)
        if m:
            tool_counts[m.group(1)] += 1
    else:
        neg_count += 1

print(f"\nDistribuicao por tool:")
for tool, count in tool_counts.most_common():
    print(f"  {tool}: {count}")
print(f"  Negativos (sem tool): {neg_count}")
