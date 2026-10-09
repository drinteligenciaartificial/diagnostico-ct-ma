"""App de Diagnostico de Marketing e Aquisicao - CT Consultoria e Assessoria.

Formato funil/quiz (uma tela por vez), no mesmo padrao do "desafio":
  1. /            -> funil (contato + perguntas do framework)
  2. /enviar      -> recebe cadastro + respostas (JSON), salva e prepara o relatorio
  3. /relatorio   -> baixa o PDF (gerado por IA)
  4. /admin       -> painel do consultor: ver storage e exportar Excel
"""
import os
import threading

from flask import (
    Flask, render_template, request, redirect, url_for, session,
    send_file, jsonify, abort,
)

import storage
import report
from config import CADASTRO_FIELDS, QUESTION_GROUPS, PAISES_DDI, iter_questions

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "ct-consultoria-marketing-dev")

# Senha simples para o painel do consultor (troque via env ADMIN_PASSWORD).
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ct2026")

# PDF pronto por lead (bytes). Re-downloads entregam o MESMO arquivo.
_REPORT_CACHE = {}
# Estado da geracao por lead: "pending" | "ready" | "error:<msg>".
_REPORT_STATUS = {}
# Cadastro + respostas por lead_id, em memoria. Guardamos aqui (e carregamos o
# lead_id na URL) para NAO depender do cookie de sessao do Flask: navegadores
# internos (Instagram/WhatsApp), modo anonimo e bloqueadores de cookie derrubam
# a sessao e faziam o /relatorio voltar pra home perdendo tudo.
_LEAD_DATA = {}
# Protege o inicio da geracao para cada lead nao disparar duas threads.
_GEN_GUARD = threading.Lock()


def _generate_report(lead_id, lead, answers):
    """Gera analise + PDF (lento, ~100s) e guarda no cache. Roda em thread."""
    try:
        analysis = report.analyze(lead, answers)
        pdf = report.build_pdf(lead, analysis)
        _REPORT_CACHE[lead_id] = pdf
        _REPORT_STATUS[lead_id] = "ready"
    except Exception as e:  # noqa: BLE001 - queremos reportar qualquer falha
        _REPORT_STATUS[lead_id] = "error:" + str(e)


def _start_report(lead_id, lead, answers):
    """Dispara a geracao em segundo plano uma unica vez por lead."""
    with _GEN_GUARD:
        if lead_id in _REPORT_STATUS:  # ja esta gerando ou pronto
            return
        if not os.environ.get("ANTHROPIC_API_KEY"):
            _REPORT_STATUS[lead_id] = "error:ANTHROPIC_API_KEY ausente"
            return
        _REPORT_STATUS[lead_id] = "pending"
    threading.Thread(
        target=_generate_report, args=(lead_id, lead, answers), daemon=True
    ).start()


@app.route("/")
def index():
    """Diagnostico em formato de funil/quiz (uma tela por vez)."""
    return render_template("funil.html", fields=CADASTRO_FIELDS,
                           groups=QUESTION_GROUPS, paises_ddi=PAISES_DDI)


@app.route("/enviar", methods=["POST"])
def enviar():
    """Recebe cadastro + respostas do funil (JSON), salva e prepara o relatorio."""
    payload = request.get_json(silent=True) or {}
    cadastro = payload.get("cadastro", {}) or {}
    answers_in = payload.get("answers", {}) or {}

    data = {f["name"]: str(cadastro.get(f["name"], "")).strip() for f in CADASTRO_FIELDS}
    faltando = [f["label"] for f in CADASTRO_FIELDS
                if f.get("required") and not data.get(f["name"])]
    if faltando:
        return jsonify({"ok": False, "erro": "Preencha: " + ", ".join(faltando)}), 400

    answers = {qid: str(answers_in.get(qid, "")).strip()
               for qid, _, _, _ in iter_questions()}

    lead_id = storage.new_id()
    storage.save_lead(lead_id, data)
    storage.save_respostas(lead_id, answers)
    # Guarda no servidor (nao no cookie) e carrega o lead_id na URL do relatorio.
    _LEAD_DATA[lead_id] = {"lead": data, "answers": answers}
    # Ja comeca a gerar o PDF em segundo plano enquanto o usuario e redirecionado.
    _start_report(lead_id, data, answers)
    return jsonify({"ok": True, "redirect": url_for("relatorio", lead_id=lead_id)})


def _nome_arquivo(lead):
    return (lead.get("empresa") or "estrategia").replace(" ", "_")


@app.route("/relatorio/<lead_id>")
def relatorio(lead_id):
    info = _LEAD_DATA.get(lead_id)
    if not info:
        return redirect(url_for("index"))
    return render_template("relatorio.html", lead=info["lead"], lead_id=lead_id)


@app.route("/relatorio/<lead_id>/status")
def relatorio_status(lead_id):
    """A pagina consulta este status (rapido) ate o PDF ficar pronto."""
    info = _LEAD_DATA.get(lead_id)
    if not info:
        return jsonify({"state": "unknown"})
    # Garante que a geracao esteja em andamento mesmo se o /enviar nao a iniciou.
    if lead_id not in _REPORT_STATUS:
        _start_report(lead_id, info["lead"], info["answers"])
    st = _REPORT_STATUS.get(lead_id, "pending")
    if st == "ready":
        return jsonify({"state": "ready"})
    if st.startswith("error:"):
        return jsonify({"state": "error", "msg": st[6:]})
    return jsonify({"state": "pending"})


@app.route("/relatorio/<lead_id>/pdf")
def relatorio_pdf(lead_id):
    import io
    info = _LEAD_DATA.get(lead_id)
    nome = _nome_arquivo(info["lead"]) if info else "estrategia"

    # Caminho normal: a pagina so chama /relatorio/pdf DEPOIS que /relatorio/status
    # devolve "ready", entao o PDF ja esta no cache e o download e instantaneo.
    cached = _REPORT_CACHE.get(lead_id)
    if cached:
        return send_file(io.BytesIO(cached), mimetype="application/pdf",
                         as_attachment=True,
                         download_name=f"Estrategia_Marketing_{nome}.pdf")

    if not info:
        return redirect(url_for("index"))

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return ("<h2>Relatório indisponível</h2><p>A chave da API da Anthropic "
                "(ANTHROPIC_API_KEY) não foi configurada. As respostas já foram salvas. "
                "Defina a chave e reinicie o app para gerar o PDF.</p>"), 503

    # Fallback (acesso direto ao link antes de ficar pronto): garante a geracao e
    # espera a thread de segundo plano terminar, sem nunca gerar duas vezes.
    _start_report(lead_id, info["lead"], info["answers"])
    import time as _time
    for _ in range(300):  # ate ~150s
        st = _REPORT_STATUS.get(lead_id, "pending")
        if st == "ready":
            break
        if st.startswith("error:"):
            return jsonify({"erro": f"Falha ao gerar a análise: {st[6:]}"}), 500
        _time.sleep(0.5)
    pdf = _REPORT_CACHE.get(lead_id)
    if pdf is None:
        return jsonify({"erro": "Tempo esgotado ao gerar o relatório."}), 504
    return send_file(io.BytesIO(pdf), mimetype="application/pdf",
                     as_attachment=True,
                     download_name=f"Estrategia_Marketing_{nome}.pdf")


# ---------------------------------------------------------------------------
# Painel do consultor
# ---------------------------------------------------------------------------
@app.route("/admin")
def admin():
    if session.get("is_admin"):
        return render_template("admin.html", backend=storage.storage_backend())
    return render_template("admin_login.html", erro=None)


@app.route("/admin/login", methods=["POST"])
def admin_login():
    if request.form.get("senha") == ADMIN_PASSWORD:
        session["is_admin"] = True
        return redirect(url_for("admin"))
    return render_template("admin_login.html", erro="Senha incorreta.")


@app.route("/admin/export")
def admin_export():
    if not session.get("is_admin"):
        abort(403)
    import io
    data = storage.export_xlsx_bytes()
    return send_file(io.BytesIO(data),
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     as_attachment=True, download_name="leads_marketing.xlsx")


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("index"))


if __name__ == "__main__":
    import threading
    import webbrowser

    port = int(os.environ.get("PORT", 5001))
    url = f"http://127.0.0.1:{port}"
    print("\n  CT Consultoria - Diagnostico de Marketing e Aquisicao")
    print(f"  Armazenamento atual: {storage.storage_backend()}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("  [aviso] ANTHROPIC_API_KEY nao definida: o funil funciona,")
        print("          mas a geracao do relatorio em PDF (IA) ficara indisponivel.")
    print(f"  Abrindo no navegador:  {url}")
    print("  Para encerrar, feche esta janela ou pressione Ctrl+C.\n")

    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    app.run(host="0.0.0.0", port=port, debug=False)
