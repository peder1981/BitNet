#!/usr/bin/env python3
"""Gera dataset v3 com:
- Todos os exemplos positivos do v1 (162)
- Mais exemplos positivos para tools com baixa cobertura
- 50+ exemplos negativos no formato correto (4 mensagens)
- Total alvo: 300+ exemplos
"""
import json
import random

random.seed(42)

# ========== EXEMPLOS POSITIVOS ADICIONAIS ==========

# consultar_base_direta (já tem 40, adicionar 10 mais variados)
extra_base_direta = [
    ("Explique a função A010TIT", "funcao A010Tit", 5),
    ("O que faz a função A010TIT?", "funcao A010Tit", 3),
    ("Como funciona a função A020TIT?", "funcao A020Tit", 8),
    ("Me mostre o código da função A020TIT", "funcao A020Tit", 5),
    ("Explique a função A030TIT", "funcao A030Tit", 3),
    ("O que faz a função A040TIT?", "funcao A040Tit", 5),
    ("Como funciona a função A050TIT?", "funcao A050Tit", 8),
    ("Me mostre o código da função A050TIT", "funcao A050Tit", 3),
    ("Explique a função A060TIT", "funcao A060Tit", 5),
    ("O que faz a função A070TIT?", "funcao A070Tit", 3),
]

# consultar_dicionario_direto (já tem 39, adicionar 10)
extra_dicionario = [
    ("Quais são os campos da tabela SA3?", "campos tabela SA3", 5),
    ("Me mostre a estrutura da tabela SA4", "campos tabela SA4", 8),
    ("Quais campos tem a tabela SB2?", "campos tabela SB2", 3),
    ("Estrutura da tabela SB7", "campos tabela SB7", 5),
    ("Quais são os campos da tabela SC1?", "campos tabela SC1", 8),
    ("Me mostre a estrutura da tabela SC2", "campos tabela SC2", 5),
    ("Quais campos tem a tabela SC3?", "campos tabela SC3", 3),
    ("Estrutura da tabela SC4", "campos tabela SC4", 8),
    ("Quais são os campos da tabela SE3?", "campos tabela SE3", 5),
    ("Me mostre a estrutura da tabela SE4", "campos tabela SE4", 3),
]

# consultar_base_interna (tem 20, adicionar 20)
extra_base_interna = [
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

# buscar_reversa_direto (tem 20, adicionar 20)
extra_reversa_direto = [
    "Como usar o skill reversa-scout?",
    "Como usar o skill reversa-archaeologist?",
    "Como usar o skill reversa-detective?",
    "Como usar o skill reversa-architect?",
    "Como usar o skill reversa-writer?",
    "Como usar o skill reversa-reviewer?",
    "Como usar o skill reversa-coding?",
    "Como usar o skill reversa-requirements?",
    "Como usar o skill reversa-plan?",
    "Como usar o skill reversa-to-do?",
    "Como usar o skill reversa-migrate?",
    "Como usar o skill reversa-forward?",
    "Como usar o skill reversa-pricing-profile?",
    "Como usar o skill reversa-pricing-size?",
    "Como usar o skill reversa-principles?",
    "Como usar o skill reversa-quality?",
    "Como usar o skill reversa-clarify?",
    "Como usar o skill reversa-audit?",
    "Como usar o skill reversa-resume?",
    "Como usar o skill reversa-extract-soul?",
]

# consultar_reversa_rag (tem 6, adicionar 24 — precisa muito!)
extra_reversa_rag = [
    "Como criar um REST endpoint em TLPP?",
    "Como gerar código MVC no Protheus?",
    "Como criar um ponto de entrada?",
    "Como documentar função AdvPL?",
    "Como migrar AdvPL para TLPP?",
    "Como criar endpoint REST com annotations?",
    "Como usar oReRest object em TLPP?",
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
    "Como implementar paginação em REST Protheus?",
    "Como gerar Swagger para API Protheus?",
    "Como usar FWFormModel em MVC?",
    "Como criar FWFormView?",
]

# mem0_search (tem 12, adicionar 12)
extra_mem0_search = [
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
]

# mem0_add (tem 10, adicionar 14)
extra_mem0_add = [
    "Anote que o cliente prefere contato por e-mail",
    "Salve que o cliente João paga em 30 dias",
    "Anote que a versão do Protheus é 12.1.33",
    "Salve que o servidor é Linux Ubuntu 22.04",
    "Anote que o banco de dados é SQL Server",
    "Salve que o cliente trabalha com o ramo varejo",
    "Anote que o fuso horário é UTC-3",
    "Salve que o idioma padrão é português",
    "Anote que o cliente tem 50 usuários",
    "Salve que a empresa usa TOTVS Protheus",
    "Anote que o responsável técnico é Carlos",
    "Salve que o prazo de entrega é 15 dias úteis",
    "Anote que o cliente quer relatório mensal",
    "Salve que o orçamento do projeto é R$ 50 mil",
]

# mem0_list (tem 5, adicionar 15 — precisa muito!)
extra_mem0_list = [
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
]

# mem0_stats (tem 5, adicionar 15 — precisa muito!)
extra_mem0_stats = [
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
]

# mem0_delete (tem 5, adicionar 10)
extra_mem0_delete = [
    "Apague a memória sobre o teste",
    "Delete a memória antiga",
    "Remova a memória do cliente João",
    "Apague a memória sobre o projeto X",
    "Delete a memória mem123",
    "Remova a anotação sobre o bug",
    "Apague a memória do fornecedor",
    "Delete a memória sobre a reunião",
    "Remova a memória do contrato",
    "Apague a anotação do orçamento",
]


def make_positive_consultar_base_direta(question, search_term, n_results):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'<tool_call>\n{{"name": "protheus-rag__consultar_base_direta", "arguments": {{"pergunta": "{search_term}", "n_results": {n_results}}}}}\n</tool_call>'},
            {"role": "user", "content": f'Resultado da ferramenta `protheus-rag__consultar_base_direta`:\n```\n[1] {search_term}.prw (score 0.88)\n// Código fonte encontrado\nUser Function {search_term}()\n...\nReturn\n\n```\nUse esse resultado para responder ao usuário em português.'},
            {"role": "assistant", "content": f"A função {search_term} é uma User Function do Protheus."},
        ]
    }


def make_positive_dicionario(question, search_term, n_results):
    table = search_term.replace("campos tabela ", "")
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'<tool_call>\n{{"name": "protheus-rag__consultar_dicionario_direto", "arguments": {{"pergunta": "{search_term}", "n_results": {n_results}}}}}\n</tool_call>'},
            {"role": "user", "content": f'Resultado da ferramenta `protheus-rag__consultar_dicionario_direto`:\n```\n[1] {table} (score 0.85)\n// Campos encontrados\n{table}_CODIGO - Código\n{table}_DESC - Descrição\n...\n\n```\nUse esse resultado para responder ao usuário em português.'},
            {"role": "assistant", "content": f"A tabela {table} possui campos como código, descrição, etc."},
        ]
    }


def make_positive_base_interna(question):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'<tool_call>\n{{"name": "protheus-rag__consultar_base_interna", "arguments": {{"pergunta": "{question}"}}}}\n</tool_call>'},
            {"role": "user", "content": f'Resultado da ferramenta `protheus-rag__consultar_base_interna`:\n```\n[1] Documentação (score 0.82)\n// Resposta interpretada\nO processo envolve várias etapas...\n\n```\nUse esse resultado para responder ao usuário em português.'},
            {"role": "assistant", "content": f"O processo funciona através de etapas integradas no Protheus."},
        ]
    }


def make_positive_reversa_direto(question):
    skill_name = question.replace("Como usar o skill ", "").replace("?", "")
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'<tool_call>\n{{"name": "protheus-rag__buscar_reversa_direto", "arguments": {{"pergunta": "skill {skill_name}", "n_results": 5}}}}\n</tool_call>'},
            {"role": "user", "content": f'Resultado da ferramenta `protheus-rag__buscar_reversa_direto`:\n```\n[1] {skill_name}.md (score 0.89)\n// Skill encontrado\n{skill_name} é responsável por...\n\n```\nUse esse resultado para responder ao usuário em português.'},
            {"role": "assistant", "content": f"O skill {skill_name} faz parte do framework Reversa."},
        ]
    }


def make_positive_reversa_rag(question):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'<tool_call>\n{{"name": "protheus-rag__consultar_reversa_rag", "arguments": {{"pergunta": "{question}"}}}}\n</tool_call>'},
            {"role": "user", "content": f'Resultado da ferramenta `protheus-rag__consultar_reversa_rag`:\n```\n[1] Reversa (score 0.86)\n// Resposta interpretada\n{question} envolve...\n\n```\nUse esse resultado para responder ao usuário em português.'},
            {"role": "assistant", "content": f"Para isso, use os recursos do framework Reversa conforme documentação."},
        ]
    }


def make_positive_mem0_search(question):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'<tool_call>\n{{"name": "protheus-rag__mem0_search", "arguments": {{"query": "{question}"}}}}\n</tool_call>'},
            {"role": "user", "content": f'Resultado da ferramenta `protheus-rag__mem0_search`:\n```\n[1] (score 0.85)\nMemória encontrada com contexto relevante.\n\n```\nUse esse resultado para responder ao usuário em português.'},
            {"role": "assistant", "content": f"Encontrei informações relevantes na memória."},
        ]
    }


def make_positive_mem0_add(question):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'<tool_call>\n{{"name": "protheus-rag__mem0_add", "arguments": {{"content": "{question}"}}}}\n</tool_call>'},
            {"role": "user", "content": f'Resultado da ferramenta `protheus-rag__mem0_add`:\n```\nMemória adicionada com sucesso.\n```\nUse esse resultado para responder ao usuário em português.'},
            {"role": "assistant", "content": f"Anotado com sucesso."},
        ]
    }


def make_positive_mem0_list(question):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'<tool_call>\n{{"name": "protheus-rag__mem0_list", "arguments": {{}}}}\n</tool_call>'},
            {"role": "user", "content": f'Resultado da ferramenta `protheus-rag__mem0_list`:\n```\nTotal: 20 memórias\n// Lista\n...\n\n```\nUse esse resultado para responder ao usuário em português.'},
            {"role": "assistant", "content": f"Temos 20 memórias armazenadas."},
        ]
    }


def make_positive_mem0_stats(question):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'<tool_call>\n{{"name": "protheus-rag__mem0_stats", "arguments": {{}}}}\n</tool_call>'},
            {"role": "user", "content": f'Resultado da ferramenta `protheus-rag__mem0_stats`:\n```\nTotal: 20 memórias\nCategorias: fact, preference, context\n...\n\n```\nUse esse resultado para responder ao usuário em português.'},
            {"role": "assistant", "content": f"A base contém 20 memórias."},
        ]
    }


def make_positive_mem0_delete(question):
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": f'<tool_call>\n{{"name": "protheus-rag__mem0_delete", "arguments": {{"memory_id": "mem123"}}}}\n</tool_call>'},
            {"role": "user", "content": f'Resultado da ferramenta `protheus-rag__mem0_delete`:\n```\nMemória removida com sucesso.\n```\nUse esse resultado para responder ao usuário em português.'},
            {"role": "assistant", "content": f"A memória foi removida."},
        ]
    }


# ========== EXEMPLOS NEGATIVOS (formato 4 mensagens) ==========

negative_qa = [
    ("Olá, como vai?", "Olá! Estou bem, obrigado. Como posso ajudar você hoje?"),
    ("Quanto é 2 + 2?", "2 + 2 é igual a 4."),
    ("Bom dia!", "Bom dia! Em que posso ser útil?"),
    ("Qual é o seu nome?", "Sou um assistente de IA especializado em Protheus e desenvolvimento."),
    ("Obrigado pela ajuda!", "De nada! Estou aqui para ajudar sempre que precisar."),
    ("Tchau!", "Até mais! Se precisar de algo, é só chamar."),
    ("Qual a capital do Brasil?", "A capital do Brasil é Brasília."),
    ("Quanto é 10 vezes 5?", "10 × 5 = 50."),
    ("Me conte uma piada.", "Por que o desenvolvedor foi ao médico? Porque tinha um bug!"),
    ("O que é AdvPL?", "AdvPL é a linguagem de programação proprietária do sistema ERP Protheus da TOTVS."),
    ("O que é TLPP?", "TLPP (TOTVS Language Plus Plus) é a evolução moderna do AdvPL, com tipagem e recursos mais avançados."),
    ("Boa noite!", "Boa noite! Se precisar de algo amanhã, estarei por aqui."),
    ("Como está o tempo hoje?", "Não tenho acesso a dados meteorológicos em tempo real, mas posso ajudar com outras questões!"),
    ("Qual é a maior empresa do Brasil?", "Historicamente, Petrobras é uma das maiores empresas brasileiras em valor de mercado."),
    ("Quem inventou o computador?", "O conceito de computador programável é atribuído a Charles Babbage, com a Máquina Analítica no século XIX."),
    ("O que é um ERP?", "ERP (Enterprise Resource Planning) é um sistema integrado de gestão empresarial que conecta todos os processos de uma organização."),
    ("Qual a diferença entre SQL e NoSQL?", "SQL é baseado em tabelas relacionais com schema fixo. NoSQL é mais flexível, usando documentos, grafos ou key-value."),
    ("Me explique o que é API.", "API (Application Programming Interface) é um conjunto de regras que permite que diferentes softwares se comuniquem entre si."),
    ("O que é um banco de dados?", "Um banco de dados é um sistema organizado para armazenar, gerenciar e recuperar informações de forma estruturada."),
    ("O que é um servidor?", "Um servidor é um computador ou programa que fornece recursos, dados ou serviços para outros computadores em uma rede."),
    ("Quanto é 100 dividido por 4?", "100 ÷ 4 = 25."),
    ("Qual é o significado de MVC?", "MVC (Model-View-Controller) é um padrão de arquitetura que separa dados, interface e lógica de controle."),
    ("O que é REST?", "REST (Representational State Transfer) é um estilo arquitetural para design de APIs web baseado em recursos e métodos HTTP."),
    ("Me explique o que é JSON.", "JSON (JavaScript Object Notation) é um formato leve de intercâmbio de dados, fácil de ler e escrever."),
    ("O que é um framework?", "Um framework é uma estrutura de código reutilizável que fornece componentes e padrões para facilitar o desenvolvimento."),
    ("Qual a diferença entre frontend e backend?", "Frontend é a interface visível do usuário. Backend é a lógica e processamento no servidor."),
    ("O que é Docker?", "Docker é uma plataforma que permite empacotar aplicações em containers, garantindo consistência em qualquer ambiente."),
    ("O que é Git?", "Git é um sistema de controle de versão distribuído que rastreia mudanças no código-fonte ao longo do tempo."),
    ("O que é um commit?", "Um commit no Git é um snapshot do estado do código em um momento específico, com uma mensagem descritiva."),
    ("Me explique o que é branch.", "Uma branch no Git é uma linha independente de desenvolvimento que permite trabalhar em funcionalidades sem afetar o código principal."),
    ("Qual a capital da França?", "A capital da França é Paris."),
    ("Quanto é 7 vezes 8?", "7 × 8 = 56."),
    ("O que é Python?", "Python é uma linguagem de programação de alto nível, interpretada e multiparadigma, conhecida pela sintaxe clara."),
    ("O que é JavaScript?", "JavaScript é uma linguagem de programação que permite implementar funcionalidades complexas em páginas web."),
    ("Qual a diferença entre Java e JavaScript?", "Java e JavaScript são linguagens completamente diferentes. Java é compilada e tipada, JavaScript é interpretada e dinâmica."),
    ("Me explique recursão.", "Recursão é quando uma função chama a si mesma para resolver um problema menor até atingir um caso base."),
    ("O que é um algoritmo?", "Um algoritmo é uma sequência finita de instruções para resolver um problema ou executar uma tarefa."),
    ("Quanto é 15 + 27?", "15 + 27 = 42."),
    ("O que é machine learning?", "Machine learning é uma área da IA onde sistemas aprendem padrões a partir de dados, sem serem explicitamente programados."),
    ("Qual o maior planeta do sistema solar?", "Júpiter é o maior planeta do sistema solar."),
    ("O que é cloud computing?", "Cloud computing é a entrega de serviços de computação pela internet, incluindo servidores, armazenamento e software."),
    ("Boa tarde!", "Boa tarde! Como posso ajudar?"),
    ("Quanto é 50 menos 23?", "50 - 23 = 27."),
    ("O que é HTML?", "HTML (HyperText Markup Language) é a linguagem de marcação padrão para criar páginas web."),
    ("O que é CSS?", "CSS (Cascading Style Sheets) é a linguagem usada para descrever a apresentação visual de documentos HTML."),
    ("Me explique o que é uma variável.", "Uma variável é um espaço nomeado na memória que armazena um valor que pode ser modificado durante a execução de um programa."),
    ("O que é Linux?", "Linux é um sistema operacional open source baseado no kernel Linux, criado por Linus Torvalds em 1991."),
    ("Quanto é 9 ao quadrado?", "9² = 81."),
    ("O que é uma API RESTful?", "Uma API RESTful é uma API que segue os princípios do REST, usando métodos HTTP e URIs para identificar recursos."),
    ("Qual a velocidade da luz?", "A velocidade da luz no vácuo é aproximadamente 299.792 km/s."),
]


def make_negative_4msg(question, answer):
    """Negativo no formato 4 mensagens: user → assistant(resposta direta) → user(confirmação) → assistant"""
    return {
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
            {"role": "user", "content": "Obrigado!"},
            {"role": "assistant", "content": "De nada! Estou aqui para ajudar."},
        ]
    }


# ========== GERAR DATASET ==========

# 1. Carregar exemplos originais
with open("data/ptbr_tools_train_large.jsonl", encoding="utf-8") as f:
    original = [json.loads(line) for line in f if line.strip()]

print(f"Originais: {len(original)}")

# 2. Gerar exemplos positivos adicionais
extras = []

for q, term, n in extra_base_direta:
    extras.append(make_positive_consultar_base_direta(q, term, n))
for q, term, n in extra_dicionario:
    extras.append(make_positive_dicionario(q, term, n))
for q in extra_base_interna:
    extras.append(make_positive_base_interna(q))
for q in extra_reversa_direto:
    extras.append(make_positive_reversa_direto(q))
for q in extra_reversa_rag:
    extras.append(make_positive_reversa_rag(q))
for q in extra_mem0_search:
    extras.append(make_positive_mem0_search(q))
for q in extra_mem0_add:
    extras.append(make_positive_mem0_add(q))
for q in extra_mem0_list:
    extras.append(make_positive_mem0_list(q))
for q in extra_mem0_stats:
    extras.append(make_positive_mem0_stats(q))
for q in extra_mem0_delete:
    extras.append(make_positive_mem0_delete(q))

print(f"Positivos adicionais: {len(extras)}")

# 3. Gerar exemplos negativos (formato 4 mensagens)
negatives = [make_negative_4msg(q, a) for q, a in negative_qa]
print(f"Negativos (4 msgs): {len(negatives)}")

# 4. Combinar tudo e embaralhar
combined = original + extras + negatives
random.shuffle(combined)

# 5. Salvar
with open("data/ptbr_tools_train_v3.jsonl", "w", encoding="utf-8") as f:
    for ex in combined:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"\nTotal dataset v3: {len(combined)} exemplos")
print(f"  Originais: {len(original)}")
print(f"  Positivos extra: {len(extras)}")
print(f"  Negativos: {len(negatives)}")

# Estatísticas por tool
from collections import Counter
import re
tool_counts = Counter()
neg_count = 0
for ex in combined:
    msgs = ex["messages"]
    assistant_msg = msgs[1]["content"] if len(msgs) > 1 else ""
    if "<tool_call>" in assistant_msg:
        m = re.search(r'"name":\s*"([^"]+)"', assistant_msg)
        if m:
            tool_counts[m.group(1)] += 1
    else:
        neg_count += 1

print(f"\nDistribuição por tool:")
for tool, count in tool_counts.most_common():
    print(f"  {tool}: {count}")
print(f"  Negativos (sem tool): {neg_count}")
print(f"  Proporção negativa: {neg_count/len(combined)*100:.1f}%")
