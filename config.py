# -*- coding: utf-8 -*-
"""Fonte unica de verdade do Diagnostico de Marketing e Aquisicao.

Baseado no "Framework Estrategico de Marketing e Aquisicao": constroi uma
estrategia de marketing e aquisicao de clientes a partir de um diagnostico
estruturado da empresa (clareza do fundador, conhecimento do mercado,
benchmark, construcao da estrategia e scorecard).

Obs.: as chaves internas (field["name"] e group["id"]) sao mantidas sem acento
porque viram nomes de colunas/ids; apenas os textos exibidos sao acentuados.
"""

# ---------------------------------------------------------------------------
# CADASTRO (captacao de lead)
# ---------------------------------------------------------------------------
FUNCOES = [
    "Sócio(a) / Proprietário(a)", "CEO / Diretor(a) Geral", "Diretor(a)", "Gerente",
    "Coordenador(a)", "Supervisor(a)", "Médico(a)", "Administrador(a)",
    "Gestor(a) de Clínica / Hospital", "Consultor(a)", "Empreendedor(a)",
    "Financeiro", "Recursos Humanos", "Comercial / Vendas", "Marketing",
    "Operações", "Tecnologia da Informação", "Analista", "Assistente / Auxiliar", "Outro",
]

FAIXAS_FATURAMENTO = [
    "Até R$ 10 mil", "R$ 10 mil a R$ 20 mil", "R$ 20 mil a R$ 50 mil",
    "R$ 50 mil a R$ 100 mil", "R$ 100 mil a R$ 1 milhão", "Mais de R$ 1 milhão",
]

# Paises com DDI (Brasil primeiro). Usado tanto no telefone quanto no endereco.
PAISES_DDI = [
    {"nome": "Brasil", "ddi": "+55"}, {"nome": "Portugal", "ddi": "+351"},
    {"nome": "Estados Unidos", "ddi": "+1"}, {"nome": "Argentina", "ddi": "+54"},
    {"nome": "Uruguai", "ddi": "+598"}, {"nome": "Paraguai", "ddi": "+595"},
    {"nome": "Chile", "ddi": "+56"}, {"nome": "Bolívia", "ddi": "+591"},
    {"nome": "Peru", "ddi": "+51"}, {"nome": "Colômbia", "ddi": "+57"},
    {"nome": "México", "ddi": "+52"}, {"nome": "Espanha", "ddi": "+34"},
    {"nome": "França", "ddi": "+33"}, {"nome": "Itália", "ddi": "+39"},
    {"nome": "Alemanha", "ddi": "+49"}, {"nome": "Reino Unido", "ddi": "+44"},
    {"nome": "Canadá", "ddi": "+1"}, {"nome": "Japão", "ddi": "+81"},
    {"nome": "China", "ddi": "+86"}, {"nome": "Austrália", "ddi": "+61"},
    {"nome": "Angola", "ddi": "+244"}, {"nome": "Moçambique", "ddi": "+258"},
    {"nome": "Outro", "ddi": "+"},
]

CADASTRO_FIELDS = [
    {"name": "nome",         "label": "Nome completo",                       "type": "text",   "required": True},
    {"name": "telefone",     "label": "Telefone / WhatsApp",                 "type": "tel",    "required": True},
    {"name": "email",        "label": "E-mail",                              "type": "email",  "required": True},
    {"name": "funcao",       "label": "Função na empresa",                   "type": "select", "required": True, "options": FUNCOES},
    {"name": "empresa",      "label": "Empresa",                             "type": "text",   "required": True},
    {"name": "pais",         "label": "País",                                "type": "pais",   "required": True, "default": "Brasil"},
    {"name": "estado",       "label": "Estado",                              "type": "estado", "required": True},
    {"name": "cidade",       "label": "Cidade",                              "type": "cidade", "required": True},
    {"name": "funcionarios", "label": "Quantos funcionários a empresa tem?", "type": "number", "required": True, "min": 0},
    {"name": "faturamento",  "label": "Faturamento médio mensal",            "type": "select", "required": True, "options": FAIXAS_FATURAMENTO},
]

# ---------------------------------------------------------------------------
# QUESTIONARIO - etapas do Framework de Marketing e Aquisicao
# ---------------------------------------------------------------------------
QUESTION_GROUPS = [
    {
        "id": "clareza",
        "titulo": "#1 CLAREZA DO FUNDADOR",
        "descricao": "Vamos testar o nível de clareza que você tem sobre o próprio negócio. "
                     "As respostas iniciam a construção da sua estratégia.",
        "perguntas": [
            "O que você vende?",
            "Para quem você vende?",
            "Em qual mercado você atua?",
            "Contra qual alternativa você compete?",
            "Com qual vantagem você compete?",
            "Com qual prova você sustenta essa vantagem?",
            "Com qual modelo de crescimento você opera hoje?",
        ],
    },
    {
        "id": "mercado",
        "titulo": "#2 CONHECIMENTO DO MERCADO",
        "descricao": "Agora testamos o quanto você conhece o mercado em que joga.",
        "perguntas": [
            "Quem está crescendo no seu mercado?",
            "Por que essas empresas estão crescendo?",
            "Onde está a margem no seu mercado?",
            "Onde existe recorrência de receita?",
            "Onde está a pressão competitiva?",
            "Que comportamento do cliente está mudando?",
        ],
    },
    {
        "id": "benchmark",
        "titulo": "#3 BENCHMARK ESTRATÉGICO",
        "descricao": "Verificamos se você utiliza fontes avançadas de benchmark para tomar decisões.",
        "perguntas": [
            {"texto": "Você utiliza materiais de Relações com Investidores (RI) — releases, "
                      "formulários de referência e apresentações trimestrais — para aprender "
                      "com empresas do seu mercado?", "tipo": "sim_nao"},
            {"texto": "Você consulta a Biblioteca de Anúncios dos concorrentes para entender "
                      "o que eles anunciam e qual estratégia utilizam?", "tipo": "sim_nao"},
            {"texto": "Você utiliza Inteligência Artificial para analisar essas informações, "
                      "sintetizar padrões e gerar perguntas estratégicas antes de decidir?", "tipo": "sim_nao"},
        ],
    },
    {
        "id": "icp",
        "titulo": "#4 QUEM VALE A PENA ATRAIR",
        "descricao": "Definição do ICP (perfil de cliente ideal) e eliminação dos clientes errados.",
        "perguntas": [
            "Liste seus 5 melhores clientes.",
            "Liste seus 5 piores clientes.",
            "O que os seus melhores clientes têm em comum?",
            "Que perfil de cliente você deveria parar de atrair?",
        ],
    },
    {
        "id": "compra",
        "titulo": "#5 COMO O CLIENTE COMPRA",
        "descricao": "Entenda o processo de decisão de compra do seu cliente.",
        "perguntas": [
            "O que a pessoa precisa entender antes de comprar de você?",
            "Onde ela prefere comprar ou conversar?",
            "Que nível de ajuda ela precisa para decidir?",
        ],
    },
    {
        "id": "valor",
        "titulo": "#6 POR QUE ESCOLHER VOCÊ",
        "descricao": "Sua proposta de valor: cliente, problema, método, prova e resultado.",
        "perguntas": [
            "Por que deveriam escolher você?",
            "Qual é a sua proposta de valor? (descreva Cliente, Problema, Método, Prova e Resultado)",
            "Qual é o seu diferencial? Se as pessoas pudessem lembrar apenas uma coisa sobre "
            "sua empresa, qual seria?",
            "Como a empresa quer ser reconhecida e o que precisa entregar para sustentar essa percepção?",
        ],
    },
    {
        "id": "canais",
        "titulo": "#7 ONDE DISPUTAR ATENÇÃO",
        "descricao": "Escolha dos canais de distribuição — o que distribuir, para quem e com qual objetivo.",
        "perguntas": [
            "O que você vai distribuir (conteúdo, oferta, prova)?",
            "Para quem você vai distribuir?",
            "Com qual objetivo você distribui (educar, gerar demanda, converter)?",
            "Para definir o canal de distribuição, vamos passar por 8 critérios. "
            "(1/8) Onde está o seu ICP (perfil de cliente ideal)?",
            {"texto": "(2/8) Nesse canal, o seu ICP está em modo compra, pesquisa ou entretenimento?",
             "tipo": "opcoes", "opcoes": ["Compra", "Pesquisa", "Entretenimento"]},
            {"texto": "(3/8) O seu ICP precisa ser educado antes de comprar?", "tipo": "sim_nao"},
            {"texto": "(4/8) O seu ICP precisa confiar antes de comprar?", "tipo": "sim_nao"},
            {"texto": "(5/8) Para esse canal, você tem verba ou tempo?", "tipo": "opcoes",
             "opcoes": ["Tenho verba", "Tenho tempo", "Tenho ambos", "Não tenho nenhum"]},
            {"texto": "(6/8) O seu concorrente domina o canal onde o seu ICP está?", "tipo": "sim_nao"},
            {"texto": "(7/8) Você consegue medir os resultados nesse canal?", "tipo": "sim_nao"},
            {"texto": "(8/8) Esse canal cabe na sua margem?", "tipo": "sim_nao"},
            "Onde você descobre novos produtos online com mais frequência?",
        ],
    },
    {
        "id": "metricas",
        "titulo": "#8 COMO SABER SE FUNCIONA",
        "descricao": "As métricas de aquisição: CAC, LTV e Payback.",
        "perguntas": [
            "Quanto custa para conquistar um cliente hoje? (CAC)",
            "Quanto você deixa de margem ao longo do tempo com um cliente? (LTV)",
            "Quanto de CAC você pode tolerar dado esse LTV?",
            "Em quanto tempo o dinheiro investido em aquisição volta? (Payback)",
        ],
    },
]


def pergunta_texto(p):
    """Uma pergunta pode ser uma string (texto livre) ou um dict tipado."""
    return p["texto"] if isinstance(p, dict) else p


def iter_questions():
    """Gera (qid, grupo_id, grupo_titulo, texto) para cada pergunta."""
    for g in QUESTION_GROUPS:
        for i, p in enumerate(g["perguntas"]):
            yield f"{g['id']}_{i}", g["id"], g["titulo"], pergunta_texto(p)


# Contexto do framework enviado para a IA gerar a analise do relatorio.
METODOLOGIAS_CONTEXTO = """
Você constrói uma ESTRATÉGIA DE MARKETING E AQUISIÇÃO a partir de um diagnóstico estruturado
da empresa. Use o Framework Estratégico de Marketing e Aquisição como base da sua análise:

- CLAREZA DO FUNDADOR: o quanto o dono entende o próprio negócio (o que vende, para quem,
  em qual mercado, contra qual alternativa, com qual vantagem, prova e modelo de crescimento).
- CONHECIMENTO DO MERCADO: quem cresce e por quê, onde está a margem, a recorrência, a pressão
  competitiva e que comportamento do cliente está mudando.
- BENCHMARK ESTRATÉGICO: uso de fontes avançadas (materiais de RI, Biblioteca de Anúncios,
  Inteligência Artificial) para aprender com o mercado.
- ICP (Perfil de Cliente Ideal): quem vale a pena atrair e quem parar de atrair, a partir dos
  melhores e piores clientes.
- JORNADA DE COMPRA: o que o cliente precisa entender, onde prefere comprar/conversar e quanto
  de ajuda precisa para decidir.
- PROPOSTA DE VALOR: estrutura Cliente > Problema > Método > Prova > Resultado, mais o diferencial
  e a percepção que a empresa quer construir.
- CANAIS / DISTRIBUIÇÃO: o que distribuir, para quem e com qual objetivo, avaliando os 8 critérios
  de escolha de canal (ICP presente? modo compra/pesquisa/entretenimento? precisa educar? precisa
  confiar? há verba ou tempo? concorrente domina? é mensurável? cabe na margem?).
- MÉTRICAS DE AQUISIÇÃO: CAC (custo de aquisição), LTV (valor no tempo) e Payback (quando o
  dinheiro volta) — que definem quanto se pode investir e quão rápido é possível crescer.
- SCORECARD DE MARKETING: 5 dimensões pontuadas de 1 a 5 (mercado, ICP, proposta de valor,
  geração/captura de demanda e economia de aquisição).
""".strip()
