"""
PETSaúde - Medical Customizations for Open WebUI
Configurações personalizadas para uso médico
"""

# Medical System Prompt
MEDICAL_SYSTEM_PROMPT = """
Você é o PETSaúde Medical Research Assistant, um sistema especializado em fornecer informações médicas baseadas em evidências científicas do PubMed.

REGRAS CRÍTICAS:
1. Responda APENAS com base em artigos científicos
2. SEMPRE cite as fontes (PMID, autores, ano)
3. NUNCA forneça diagnósticos pessoais
4. SEMPRE inclua disclaimer médico
5. Em emergências, oriente procurar atendimento imediato

ESTRUTURA DE RESPOSTA:
- Resumo das evidências
- Citações completas
- Disclaimer de segurança

⚠️ Esta informação é apenas para fins educacionais e de pesquisa.
"""

# Medical Disclaimer
MEDICAL_DISCLAIMER = """
⚠️ AVISO IMPORTANTE: Esta informação é baseada em literatura científica e tem propósito exclusivamente educacional.
Não substitui aconselhamento médico profissional. Sempre consulte profissionais de saúde qualificados para decisões médicas.
"""

# Emergency Detection Keywords
EMERGENCY_KEYWORDS = [
    "chest pain", "dor no peito",
    "can't breathe", "não consigo respirar",
    "stroke", "derrame", "avc",
    "heart attack", "infarto",
    "overdose", "overdose",
    "severe bleeding", "sangramento grave",
    "unconscious", "inconsciente"
]

# Blocked Terms (não permitir queries sobre)
BLOCKED_TERMS = [
    "how to make drugs",
    "suicide methods",
    "self harm",
    "illegal substances"
]

# Custom UI Colors for Medical Theme
UI_THEME = {
    "primary_color": "#2E7D32",  # Medical green
    "secondary_color": "#1565C0",  # Medical blue
    "warning_color": "#F57C00",  # Orange for warnings
    "danger_color": "#D32F2F",  # Red for emergencies
    "background": "#FAFAFA",
    "text_color": "#212121"
}

# Custom Messages
MESSAGES = {
    "welcome": "Bem-vindo ao PETSaúde! Sou um assistente de pesquisa médica baseado em evidências. Como posso ajudar você hoje?",
    "emergency": "⚠️ SE ESTA É UMA EMERGÊNCIA MÉDICA, LIGUE IMEDIATAMENTE PARA O SAMU (192) OU PROCURE O PRONTO-SOCORRO MAIS PRÓXIMO!",
    "no_diagnosis": "Não posso fornecer diagnósticos pessoais. Por favor, consulte um profissional de saúde.",
    "citation_required": "Todas as informações médicas devem ser baseadas em literatura científica com citações adequadas."
}

# Model Configuration
MODEL_CONFIG = {
    "default_model": "medical-qwen:latest",
    "temperature": 0.1,  # Baixa temperatura para respostas mais consistentes
    "max_tokens": 1024,
    "top_p": 0.9,
    "repeat_penalty": 1.1
}

# PubMed Integration Settings
PUBMED_CONFIG = {
    "enabled": True,
    "max_results": 10,
    "years_back": 5,
    "quality_threshold": 0.7,
    "preferred_types": [
        "Systematic Review",
        "Meta-Analysis",
        "Randomized Controlled Trial"
    ]
}

# Safety Features
SAFETY_CONFIG = {
    "enable_guard": True,
    "guard_threshold": 0.9,
    "require_citations": True,
    "require_disclaimer": True,
    "detect_emergencies": True,
    "block_personal_medical": True
}

# Custom Functions for Medical Validation
def is_emergency(query: str) -> bool:
    """Detecta se a query contém situação de emergência"""
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in EMERGENCY_KEYWORDS)

def is_blocked(query: str) -> bool:
    """Verifica se a query contém termos bloqueados"""
    query_lower = query.lower()
    return any(term in query_lower for term in BLOCKED_TERMS)

def add_medical_disclaimer(response: str) -> str:
    """Adiciona disclaimer médico à resposta"""
    if MEDICAL_DISCLAIMER not in response:
        response += f"\n\n{MEDICAL_DISCLAIMER}"
    return response

def validate_citations(response: str) -> bool:
    """Verifica se a resposta contém citações adequadas"""
    # Procura por padrões de citação como [Author et al., Year, PMID: xxxxx]
    import re
    citation_pattern = r'\[[\w\s]+et al\.,\s+\d{4},\s+PMID:\s+\d+\]'
    return bool(re.search(citation_pattern, response))