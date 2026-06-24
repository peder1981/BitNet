"""Tool engine — injeta tools no prompt e parseia tool calls do modelo.

Estratégia dupla (robusta para modelos 1.58bit sem fine-tune de tools):
1. System prompt PT-BR ensinando o formato <tool_call>{json}</tool_call>
2. Parser tolerante: aceita o bloco oficial, JSON solto ou cercas de código

Funciona com Falcon3-Instruct (chatml) e Llama. Quando o adapter QLoRA
PT-BR+tools estiver treinado, o formato já é o nativo do dataset.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from studio.server.mcp_bridge import McpTool

TOOL_SYSTEM_PROMPT_PTBR = """\
Você é um assistente fluente em português brasileiro com acesso a ferramentas.

# Ferramentas disponíveis

{tools_block}

# Como usar uma ferramenta

Quando precisar de informação externa, responda APENAS com o bloco:

<tool_call>
{{"name": "<nome_da_ferramenta>", "arguments": {{<argumentos JSON>}}}}
</tool_call>

Regras:
- Use uma ferramenta por vez e aguarde o resultado antes de continuar.
- Se a pergunta não precisar de ferramenta, responda diretamente em PT-BR.
- Nunca invente resultados de ferramentas.
- Após receber o resultado (mensagem com "Resultado da ferramenta"), \
responda ao usuário em português claro e objetivo, citando os dados obtidos.
"""

_TOOL_CALL_RE = re.compile(
    r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL
)
_TOOL_CALL_OPEN_RE = re.compile(
    r"<tool_call>\s*(.*)", re.DOTALL
)
_CODE_FENCE_RE = re.compile(
    r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", re.DOTALL
)


def _extract_json(text: str) -> str | None:
    """Extrai o primeiro objeto JSON válido de um texto."""
    # Método 1: procura bloco { ... } balanceado
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return text[start : i + 1]
    # Método 2: regex simples como fallback
    m = re.search(r"\{[\s\S]*?\}", text)
    if m:
        return m.group(0)
    return None


def _extract_truncated_json(text: str) -> str | None:
    """Tenta extrair JSON mesmo truncado (sem fechamento de braces)."""
    # Procura início de objeto JSON
    start = text.find("{")
    if start == -1:
        return None
    # Tenta balanced braces primeiro
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    # Se truncado, retorna o que tem até o final (se tiver conteúdo significativo)
    truncated = text[start:].strip()
    if len(truncated) > 10 and '"name"' in truncated:
        return truncated
    return None


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    raw: str


def render_tools_block(tools: list[McpTool]) -> str:
    """Bloco compacto de tools para o system prompt.

    Compacto por design: com kernels i2_s (batch=1) cada token do prompt
    custa um forward pass completo — descrições longas custam minutos.
    """
    if not tools:
        return "(nenhuma ferramenta disponível)"
    lines = []
    for t in tools:
        desc = " ".join(t.description.split())[:120]
        props = t.input_schema.get("properties", {})
        required = t.input_schema.get("required", [])
        args = ", ".join(
            f"{k}{'*' if k in required else ''}" for k in props
        ) or "sem argumentos"
        lines.append(f"- {t.qualified_name}({args}): {desc}")
    return "\n".join(lines)


def build_system_prompt(tools: list[McpTool], extra: str = "") -> str:
    prompt = TOOL_SYSTEM_PROMPT_PTBR.format(tools_block=render_tools_block(tools))
    if extra:
        prompt += f"\n# Instruções adicionais\n{extra}\n"
    return prompt


def _normalize_tool_name(name: str, known_tools: set[str]) -> str | None:
    """Normaliza o nome da tool: tenta match exato, depois com dashes->underscores."""
    if name in known_tools:
        return name
    # Modelo gera protheus-rag-mem0-stats em vez de protheus-rag__mem0_stats
    normalized = name.replace("-", "__", 1).replace("-", "_", 1)
    if normalized in known_tools:
        return normalized
    # Tentativa mais agressiva: substituir todos os dashes aps o prefixo
    if name.startswith("protheus-rag-"):
        alt = "protheus-rag__" + name[len("protheus-rag-"):].replace("-", "_")
        if alt in known_tools:
            return alt
    return None


def _try_parse(raw: str, known_tools: set[str]) -> ToolCall | None:
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        # Tentativa para JSON truncado: extrair nome via regex
        name_match = re.search(r'"name"\s*:\s*"([^"]+)"', raw)
        if name_match:
            name = _normalize_tool_name(name_match.group(1), known_tools)
            if not name:
                return None
            # Tenta extrair arguments também
            args_match = re.search(r'"arguments"\s*:\s*(\{[^}]*(?:\}[^}]*)*)', raw)
            args = {}
            if args_match:
                try:
                    args = json.loads(args_match.group(1))
                except json.JSONDecodeError:
                    pass
            return ToolCall(name=name, arguments=args or {}, raw=raw)
        return None
    if not isinstance(obj, dict):
        return None
    name = obj.get("name")
    if not name:
        return None
    name = _normalize_tool_name(name, known_tools)
    if not name:
        return None
    args = obj.get("arguments", obj.get("parameters", {}))
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {"input": args}
    return ToolCall(name=name, arguments=args or {}, raw=raw)


def parse_tool_call(text: str, tools: list[McpTool]) -> ToolCall | None:
    """Extrai a primeira tool call válida da resposta do modelo.

    Ordem de tentativa:
    1. <tool_call>...</tool_call>  (formato ensinado)
    2. <tool_call>... (truncado, sem fechamento)
    3. ```json ... ```             (modelos que cercam com código)
    4. JSON puro na resposta toda  (modelos minimalistas)
    """
    known = {t.qualified_name for t in tools}

    # 1. Bloco completo <tool_call>...</tool_call>
    for m in _TOOL_CALL_RE.finditer(text):
        raw = m.group(1)
        json_str = _extract_json(raw)
        if json_str:
            tc = _try_parse(json_str, known)
            if tc:
                return tc

    # 2. <tool_call> aberto (truncado, sem </tool_call>)
    m = _TOOL_CALL_OPEN_RE.search(text)
    if m:
        raw = m.group(1)
        json_str = _extract_truncated_json(raw)
        if json_str:
            tc = _try_parse(json_str, known)
            if tc:
                return tc

    # 2b. Tag com nome mas sem JSON braces (modelo gera apenas o nome)
    m2 = _TOOL_CALL_OPEN_RE.search(text)
    if m2:
        raw2 = m2.group(1)
        name_match2 = re.search(r'"name"\s*:\s*"([^"]+)"', raw2)
        if not name_match2:
            # Tenta extrair nome diretamente do texto apos a tag
            name_match2 = re.search(r'(protheus-rag[^\s"\']+)', raw2)
        if name_match2:
            name = _normalize_tool_name(name_match2.group(1).strip('"'), known)
            if name:
                return ToolCall(name=name, arguments={}, raw=raw2)

    # 3. Cercas de código
    for m in _CODE_FENCE_RE.finditer(text):
        tc = _try_parse(m.group(1), known)
        if tc:
            return tc

    # 4. JSON puro
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        tc = _try_parse(stripped, known)
        if tc:
            return tc

    # 5. Fallback: qualquer JSON com "name" no texto
    json_str = _extract_json(text)
    if json_str:
        tc = _try_parse(json_str, known)
        if tc:
            return tc

    # 6. Fallback extremo: regex direto para nome no texto
    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', text)
    if name_match:
        name = _normalize_tool_name(name_match.group(1), known)
        if name:
            return ToolCall(name=name, arguments={}, raw=text)

    return None


MAX_TOOL_RESULT_CHARS = 1800  # batch=1: resultado longo = prompt eval lento


def format_tool_result(tool_name: str, result: str) -> str:
    """Mensagem (role=user no template chatml simples) com o resultado."""
    if len(result) > MAX_TOOL_RESULT_CHARS:
        result = result[:MAX_TOOL_RESULT_CHARS] + "\n[… truncado]"
    return (
        f"Resultado da ferramenta `{tool_name}`:\n"
        f"```\n{result}\n```\n"
        f"Use esse resultado para responder ao usuário em português."
    )


# ========== Parser v2 — features avancadas ==========

def parse_all_tool_calls(text: str, tools: list[McpTool]) -> list[ToolCall]:
    """Extrai TODAS as tool calls validas da resposta (multi-tool)."""
    known = {t.qualified_name for t in tools}
    calls = []

    # 1. Blocos completos
    for m in _TOOL_CALL_RE.finditer(text):
        raw = m.group(1)
        json_str = _extract_json(raw)
        if json_str:
            tc = _try_parse(json_str, known)
            if tc:
                calls.append(tc)

    # 2. Blocos truncados (apenas se nao encontrou completos)
    if not calls:
        for m in _TOOL_CALL_OPEN_RE.finditer(text):
            raw = m.group(1)
            json_str = _extract_truncated_json(raw)
            if json_str:
                tc = _try_parse(json_str, known)
                if tc:
                    calls.append(tc)

    # 3. Fallback: JSON solto no texto
    if not calls:
        json_str = _extract_json(text)
        if json_str:
            tc = _try_parse(json_str, known)
            if tc:
                calls.append(tc)

    # Deduplicar por nome (mantem primeira ocorrencia)
    seen = set()
    unique = []
    for tc in calls:
        if tc.name not in seen:
            seen.add(tc.name)
            unique.append(tc)

    return unique


# Palavras-gatilho que indicam necessidade de ferramenta
_TOOL_TRIGGERS = {
    "protheus-rag__consultar_base_direta": [
        "funcao", "function", "codigo fonte", "source", "fonte", "rotina",
        "implementacao", "mafis", "mafiscal", "a010", "a020", "a030",
        "u_", "user function",
    ],
    "protheus-rag__consultar_dicionario_direto": [
        "campos", "tabela", "dicionario", "estrutura", "sx3", "sx2",
        "indice", "six",
    ],
    "protheus-rag__consultar_base_interna": [
        "como funciona", "explique", "processo", "modulo", "faturamento",
        "compras", "estoque", "contabil", "financeiro", "fluxo",
    ],
    "protheus-rag__buscar_reversa_direto": [
        "skill", "reversa", "agente", "scout", "archaeologist",
        "detective", "architect", "writer", "reviewer",
    ],
    "protheus-rag__consultar_reversa_rag": [
        "como criar", "como gerar", "como usar", "tlpp", "rest",
        "endpoint", "mvc", "ponto de entrada", "protheusdoc",
        "migrar", "advpl para", "named parameters", "try-catch",
    ],
    "protheus-rag__mem0_search": [
        "o que sabemos", "buscar", "recuperar", "lembramos",
        "anotado", "memoria sobre", "informacoes sobre",
    ],
    "protheus-rag__mem0_add": [
        "anote", "salve", "registre", "grave", "guarde",
    ],
    "protheus-rag__mem0_list": [
        "liste", "mostre", "lista", "quais", "ver todas",
        "listar", "mostrar",
    ],
    "protheus-rag__mem0_stats": [
        "quantas", "estatisticas", "total", "numero", "tamanho",
        "quantos", "resumo estatistico",
    ],
    "protheus-rag__mem0_delete": [
        "apague", "delete", "remova", "exclua", "limpe",
    ],
}

# Palavras que indicam que NAO precisa de ferramenta
_NO_TOOL_INDICATORS = [
    "obrigado", "ola", "oi", "bom dia", "boa tarde", "boa noite",
    "tchau", "quanto e", "qual a capital", "piada",
    "definicao", "o que e", "significado",
]


def should_use_tool(text: str, tools: list[McpTool]) -> str | None:
    """Heuristica de confianca: sugere qual tool usar baseado no texto.
    Retorna o nome da tool sugerida, ou None se nao precisa de tool.
    """
    text_lower = text.lower().strip()

    # Verificar indicadores de nao-tool primeiro (word boundary para evitar match parcial)
    for indicator in _NO_TOOL_INDICATORS:
        if re.search(r'\b' + re.escape(indicator) + r'\b', text_lower):
            return None

    # Verificar matematica simples (numeros + operador)
    if re.search(r'\d+\s*[+\-*/x]\s*\d+', text_lower):
        return None

    # Verificar triggers de cada tool
    best_tool = None
    best_score = 0

    for tool_name, triggers in _TOOL_TRIGGERS.items():
        score = sum(1 for t in triggers if t in text_lower)
        if score > best_score:
            best_score = score
            best_tool = tool_name

    if best_score >= 1:
        return best_tool
    return None


def build_retry_prompt(original_response: str, tools: list[McpTool]) -> str:
    """Constroi um prompt de correcao quando o modelo gera tool call malformada."""
    tool_names = [t.qualified_name for t in tools]
    tools_str = "\n".join(f"- {name}" for name in tool_names)

    return (
        f"Sua resposta anterior continha uma chamada de ferramenta malformada:\n"
        f"{original_response[:200]}\n\n"
        f"Ferramentas disponiveis (use o nome EXATO):\n{tools_str}\n\n"
        f"Responda APENAS com o bloco no formato correto:\n"
        f'{{"name": "<nome_exato>", "arguments": {{...}}}}\n'
    )
