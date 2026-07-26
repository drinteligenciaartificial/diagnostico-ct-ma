"""Geracao do relatorio de Diagnostico de Marketing e Aquisicao.

1. analyze() envia cadastro + respostas para a Claude API e recebe uma estrategia
   estruturada (clareza, ICP, proposta de valor, canais, metricas, scorecard e
   quadro de resumo).
2. build_pdf() renderiza essa analise num PDF A4 usando o papel timbrado da CT
   (assets/letterhead.png) como fundo de cada pagina.
"""
import os
import io
import datetime as dt

from config import METODOLOGIAS_CONTEXTO, CADASTRO_FIELDS, iter_questions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LETTERHEAD = os.path.join(BASE_DIR, "assets", "letterhead.png")

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

NAVY = "#16263A"
TEAL = "#1f6f78"


# ---------------------------------------------------------------------------
# 1) Analise com Claude
# ---------------------------------------------------------------------------
def _build_prompt(lead, answers):
    linhas = []
    for f in CADASTRO_FIELDS:
        linhas.append(f"- {f['label']}: {lead.get(f['name'], '')}")
    cadastro_txt = "\n".join(linhas)

    qa = []
    grupo_atual = None
    for qid, gid, gtitulo, texto in iter_questions():
        if gtitulo != grupo_atual:
            grupo_atual = gtitulo
            qa.append(f"\n[{gtitulo}]")
        resp = str(answers.get(qid, "")).strip() or "(sem resposta)"
        qa.append(f"P: {texto}\nR: {resp}")
    qa_txt = "\n".join(qa)

    return f"""Você é um estrategista sênior de marketing e aquisição da CT - Consultoria e
Assessoria, liderada pelo Dr. Carlos Torres. Produza um DIAGNÓSTICO DE MARKETING E
AQUISIÇÃO profissional, em português do Brasil, com base nas respostas de um cliente.

{METODOLOGIAS_CONTEXTO}

== DADOS DO CLIENTE ==
{cadastro_txt}

== RESPOSTAS DO DIAGNÓSTICO ==
{qa_txt}

Analise as respostas e registre a estratégia chamando a ferramenta "registrar_estrategia".
Seja concreto, cite dados informados pelo cliente e evite generalidades. Escreva todos os
textos em português do Brasil, com acentuação correta.

Regras:
- No "scorecard", avalie EXATAMENTE as 5 dimensões do Scorecard de Marketing (mercado e alavancas
  da categoria; ICP e quem evitar; proposta de valor com provas; origem/geração e captura de
  demanda; economia de aquisição — CAC, conversão e recompra). Para cada dimensão, atribua uma
  nota de 1 a 5 INFERIDA a partir das respostas do cliente ao questionário, onde 1 = menor nível
  de clareza e consciência sobre o item e 5 = maior nível de clareza e consciência. O cliente NÃO
  se autoavaliou; a nota é o seu julgamento como especialista. Justifique cada nota de forma
  objetiva, citando o que a resposta revela.
- Em "proposta_valor", preencha os 5 campos (cliente, problema, método, prova, resultado).
- Em "icp", diga claramente quem atrair e quem parar de atrair.
- Em "canais", recomende de 2 a 4 canais priorizados, cada um com a justificativa ligada
  aos 8 critérios de escolha de canal.
- Em "metricas", comente CAC, LTV e Payback com base no que foi informado (aponte lacunas
  se o cliente não souber os números).
- Em "recomendacoes", traga exatamente 3 recomendações prioritárias fundamentadas nas
  MELHORES PRÁTICAS de marketing e aquisição (posicionamento e proposta de valor clara,
  foco no ICP certo, geração e captura de demanda, escolha de canais mensuráveis e economia
  de aquisição saudável — CAC, LTV e Payback). Cada recomendação deve ser acionável e
  conectada às respostas e ao contexto do cliente, nunca genérica.
- Em "quadro_resumo", RESUMA de forma curta e direta o que as respostas do cliente revelaram
  em cada um dos 8 pontos (1 a 2 frases por ponto, sintetizando o que ele mesmo respondeu no
  questionário). Não invente dados que ele não informou; quando algo ficar indefinido, diga
  que ainda precisa ser definido.
- Em "conclusao", escreva um fechamento objetivo dizendo, em ordem de prioridade, O QUE A
  EMPRESA DEVE FAZER PRIMEIRO — os primeiros passos concretos a partir deste diagnóstico — e
  termine com um convite natural para procurar o apoio do Dr. Carlos Torres e da CT
  Consultoria para resolver esse desafio, sem soar como propaganda forçada."""


_LISTA = {"type": "array", "items": {"type": "string"}}

_ESTRATEGIA_TOOL = {
    "name": "registrar_estrategia",
    "description": "Registra a estrategia de marketing e aquisicao estruturada da empresa.",
    "input_schema": {
        "type": "object",
        "properties": {
            "resumo_executivo": {"type": "string"},
            "clareza_fundador": {"type": "string"},
            "conhecimento_mercado": {"type": "string"},
            "icp": {
                "type": "object",
                "properties": {"atrair": _LISTA, "evitar": _LISTA},
                "required": ["atrair", "evitar"],
            },
            "proposta_valor": {
                "type": "object",
                "properties": {
                    "cliente": {"type": "string"},
                    "problema": {"type": "string"},
                    "metodo": {"type": "string"},
                    "prova": {"type": "string"},
                    "resultado": {"type": "string"},
                    "diferencial": {"type": "string"},
                },
                "required": ["cliente", "problema", "metodo", "prova", "resultado", "diferencial"],
            },
            "canais": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "canal": {"type": "string"},
                        "objetivo": {"type": "string"},
                        "justificativa": {"type": "string"},
                    },
                    "required": ["canal", "objetivo", "justificativa"],
                },
            },
            "metricas": {
                "type": "object",
                "properties": {
                    "cac": {"type": "string"},
                    "ltv": {"type": "string"},
                    "payback": {"type": "string"},
                },
                "required": ["cac", "ltv", "payback"],
            },
            "scorecard": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "dimensao": {"type": "string"},
                        "nota": {"type": "integer"},
                        "justificativa": {"type": "string"},
                    },
                    "required": ["dimensao", "nota", "justificativa"],
                },
            },
            "quadro_resumo": {
                "type": "object",
                "properties": {
                    "jogo": {"type": "string"},
                    "conquistar": {"type": "string"},
                    "dor": {"type": "string"},
                    "escolhidos": {"type": "string"},
                    "aparecer": {"type": "string"},
                    "pagar": {"type": "string"},
                    "funcionando": {"type": "string"},
                    "priorizar": {"type": "string"},
                },
                "required": ["jogo", "conquistar", "dor", "escolhidos",
                             "aparecer", "pagar", "funcionando", "priorizar"],
            },
            "recomendacoes": _LISTA,
            "conclusao": {"type": "string"},
        },
        "required": ["resumo_executivo", "clareza_fundador", "conhecimento_mercado", "icp",
                     "proposta_valor", "canais", "metricas", "scorecard", "quadro_resumo",
                     "recomendacoes", "conclusao"],
    },
}


def analyze(lead, answers):
    """Chama a Claude API (saida estruturada via tool-use) e retorna o dict da analise."""
    from anthropic import Anthropic

    client = Anthropic()  # usa ANTHROPIC_API_KEY do ambiente
    msg = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        tools=[_ESTRATEGIA_TOOL],
        tool_choice={"type": "tool", "name": "registrar_estrategia"},
        messages=[{"role": "user", "content": _build_prompt(lead, answers)}],
    )
    for block in msg.content:
        if block.type == "tool_use" and block.name == "registrar_estrategia":
            return block.input
    raise RuntimeError("A IA nao retornou a estrategia estruturada esperada.")


# ---------------------------------------------------------------------------
# 2) PDF com papel timbrado
# ---------------------------------------------------------------------------
def _draw_letterhead(canvas, doc):
    from reportlab.lib.pagesizes import A4

    w, h = A4
    if os.path.exists(LETTERHEAD):
        canvas.drawImage(LETTERHEAD, 0, 0, width=w, height=h,
                         preserveAspectRatio=False, mask="auto")


def build_pdf(lead, analysis):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
    from reportlab.platypus import (
        BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
        Table, TableStyle, ListFlowable, ListItem,
    )

    buf = io.BytesIO()
    w, h = A4
    # margens evitam o logo do topo e a barra do rodape do papel timbrado
    frame = Frame(22 * mm, 18 * mm, w - 44 * mm, h - 18 * mm - 52 * mm, id="body")
    doc = BaseDocTemplate(buf, pagesize=A4,
                          title="Diagnostico de Marketing e Aquisicao - CT Consultoria")
    doc.addPageTemplates([PageTemplate(id="ct", frames=[frame], onPage=_draw_letterhead)])

    ss = getSampleStyleSheet()
    navy = colors.HexColor(NAVY)
    teal = colors.HexColor(TEAL)

    h1 = ParagraphStyle("h1", parent=ss["Title"], textColor=navy, fontSize=19,
                        spaceAfter=4, alignment=TA_CENTER)
    sub = ParagraphStyle("sub", parent=ss["Normal"], textColor=teal, fontSize=11,
                         alignment=TA_CENTER, spaceAfter=2)
    sec = ParagraphStyle("sec", parent=ss["Heading2"], textColor=colors.white,
                         backColor=navy, fontSize=12, leading=17, spaceBefore=14,
                         spaceAfter=8, leftIndent=0, rightIndent=0,
                         borderPadding=(5, 8, 5, 8))
    body = ParagraphStyle("body", parent=ss["Normal"], fontSize=10, leading=15,
                          alignment=TA_JUSTIFY, textColor=colors.HexColor("#222222"))
    bullet = ParagraphStyle("bul", parent=body, leftIndent=4)
    cell = ParagraphStyle("cell", parent=ss["Normal"], fontSize=8.5, leading=11)
    cellh = ParagraphStyle("cellh", parent=cell, textColor=colors.white,
                           fontName="Helvetica-Bold")

    story = []

    def P(t, st=body):
        story.append(Paragraph(t, st))

    def paras(txt):
        for par in str(txt or "").split("\n"):
            if par.strip():
                P(par.strip())

    def bullets(items):
        items = [i for i in (items or []) if str(i).strip()]
        if not items:
            P("<i>Nenhum item identificado.</i>")
            return
        story.append(ListFlowable(
            [ListItem(Paragraph(str(i), bullet), leftIndent=10) for i in items],
            bulletType="bullet", bulletColor=teal, start="•",
        ))

    # Cabecalho do relatorio
    story.append(Spacer(1, 4))
    P("DIAGNÓSTICO DE MARKETING E AQUISIÇÃO", h1)
    P("CT - Consultoria e Assessoria | Dr. Carlos Torres", sub)
    data_str = dt.datetime.now().strftime("%d/%m/%Y")
    P(f"Empresa: <b>{lead.get('empresa','')}</b> &nbsp;&nbsp; Responsável: "
      f"<b>{lead.get('nome','')}</b> &nbsp;&nbsp; Data: <b>{data_str}</b>", sub)
    story.append(Spacer(1, 6))

    # Resumo executivo
    P("RESUMO EXECUTIVO", sec)
    paras(analysis.get("resumo_executivo"))

    # Clareza e mercado
    P("CLAREZA DO FUNDADOR E LEITURA DE MERCADO", sec)
    paras(analysis.get("clareza_fundador"))
    story.append(Spacer(1, 4))
    paras(analysis.get("conhecimento_mercado"))

    # ICP
    P("PERFIL DE CLIENTE IDEAL (ICP)", sec)
    icp = analysis.get("icp", {}) or {}
    P("<b>Quem atrair</b>")
    bullets(icp.get("atrair"))
    P("<b>Quem parar de atrair</b>")
    bullets(icp.get("evitar"))

    # Proposta de valor
    P("PROPOSTA DE VALOR", sec)
    pv = analysis.get("proposta_valor", {}) or {}
    pv_rows = [
        [Paragraph("<b>Cliente</b>", cellh), Paragraph(str(pv.get("cliente", "") or "—"), cell)],
        [Paragraph("<b>Problema</b>", cellh), Paragraph(str(pv.get("problema", "") or "—"), cell)],
        [Paragraph("<b>Método</b>", cellh), Paragraph(str(pv.get("metodo", "") or "—"), cell)],
        [Paragraph("<b>Prova</b>", cellh), Paragraph(str(pv.get("prova", "") or "—"), cell)],
        [Paragraph("<b>Resultado</b>", cellh), Paragraph(str(pv.get("resultado", "") or "—"), cell)],
        [Paragraph("<b>Diferencial</b>", cellh), Paragraph(str(pv.get("diferencial", "") or "—"), cell)],
    ]
    lblw = 30 * mm
    pvt = Table(pv_rows, colWidths=[lblw, (w - 44 * mm) - lblw])
    pvt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), navy),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white, colors.HexColor("#f3f6f8")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(pvt)

    # Canais
    P("ONDE DISPUTAR ATENÇÃO (CANAIS)", sec)
    canais = analysis.get("canais", []) or []
    if canais:
        can_rows = [[Paragraph("Canal", cellh), Paragraph("Objetivo", cellh),
                     Paragraph("Por quê", cellh)]]
        for c in canais:
            can_rows.append([
                Paragraph(str(c.get("canal", "")), cell),
                Paragraph(str(c.get("objetivo", "")), cell),
                Paragraph(str(c.get("justificativa", "")), cell),
            ])
        tot = w - 44 * mm
        ct = Table(can_rows, colWidths=[tot * 0.24, tot * 0.26, tot * 0.50])
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6f8")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ct)
    else:
        P("<i>Nenhum canal recomendado.</i>")

    # Metricas
    P("MÉTRICAS DE AQUISIÇÃO (CAC · LTV · PAYBACK)", sec)
    m = analysis.get("metricas", {}) or {}
    P(f"<b>CAC:</b> {m.get('cac','') or '—'}")
    P(f"<b>LTV:</b> {m.get('ltv','') or '—'}")
    P(f"<b>Payback:</b> {m.get('payback','') or '—'}")

    # Scorecard
    P("SCORECARD DE MARKETING", sec)
    sc = analysis.get("scorecard", []) or []
    sc_rows = [[Paragraph("Dimensão", cellh), Paragraph("Nota", cellh),
                Paragraph("Justificativa", cellh)]]
    for item in sc:
        sc_rows.append([
            Paragraph(str(item.get("dimensao", "")), cell),
            Paragraph(f"<b>{item.get('nota','')}/5</b>", cell),
            Paragraph(str(item.get("justificativa", "")), cell),
        ])
    tot = w - 44 * mm
    st_ = Table(sc_rows, colWidths=[tot * 0.34, 16 * mm, tot - tot * 0.34 - 16 * mm])
    st_.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), navy),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f6f8")]),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(st_)

    # Quadro de resumo (8 pontos de clareza)
    P("QUADRO DE RESUMO", sec)
    qr = analysis.get("quadro_resumo", {}) or {}
    pontos = [
        ("Qual jogo vamos jogar?", "jogo"),
        ("Quem queremos conquistar?", "conquistar"),
        ("Que dor resolvemos melhor?", "dor"),
        ("Por que seremos escolhidos?", "escolhidos"),
        ("Onde vamos aparecer?", "aparecer"),
        ("Quanto podemos pagar para crescer?", "pagar"),
        ("Como saber se está funcionando?", "funcionando"),
        ("O que vamos priorizar agora?", "priorizar"),
    ]
    qr_rows = []
    for pergunta, key in pontos:
        qr_rows.append([Paragraph(f"<b>{pergunta}</b>", cell),
                        Paragraph(str(qr.get(key, "") or "—"), cell)])
    qw = 55 * mm
    qt = Table(qr_rows, colWidths=[qw, (w - 44 * mm) - qw])
    qt.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef5f5")),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white, colors.HexColor("#f3f6f8")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(qt)

    # Recomendacoes
    P("RECOMENDAÇÕES PRIORITÁRIAS", sec)
    bullets(analysis.get("recomendacoes"))

    # Conclusao
    P("CONCLUSÃO", sec)
    paras(analysis.get("conclusao"))

    # CTA final
    cta = ParagraphStyle("cta", parent=body, alignment=TA_CENTER, fontSize=11,
                         leading=16, textColor=navy, backColor=colors.HexColor("#eef5f5"),
                         borderColor=teal, borderWidth=1, borderPadding=(10, 10, 10, 10),
                         spaceBefore=16)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Quer transformar esta estratégia em um plano de aquisição concreto?</b><br/>"
        "Entre em contato com o Dr. Carlos Torres e construa, passo a passo, o plano "
        "de marketing e aquisição de clientes da sua empresa.", cta))

    doc.build(story)
    buf.seek(0)
    return buf.read()
