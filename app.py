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

# guarda em memoria a ultima analise gerada por sessao, para o download do PDF
_REPORT_CACHE = {}

# locks por lead: garantem que duas requisicoes simultaneas de /relatorio/pdf
# (ex.: download automatico + clique no botao) NAO disparem duas geracoes. A
# segunda espera a primeira terminar e reaproveita o PDF do cache.
_REPORT_LOCKS = {}
_REPORT_LOCKS_GUARD = threading.Lock()


def _lead_lock(lead_id):
    with _REPORT_LOCKS_GUARD:
        lock = _REPORT_LOCKS.get(lead_id)
        if lock is None:
            lock = threading.Lock()
            _REPORT_LOCKS[lead_id] = lock
        return lock


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
    session["lead_id"] = lead_id
    session["lead"] = data
    session["answers"] = answers
    return jsonify({"ok": True, "redirect": url_for("relatorio")})


@app.route("/relatorio")
def relatorio():
    if not session.get("answers"):
        return redirect(url_for("index"))
    return render_template("relatorio.html", lead=session.get("lead", {}))


@app.route("/relatorio/pdf")
def relatorio_pdf():
    if not session.get("answers"):
        return redirect(url_for("index"))
    lead = session.get("lead", {})
    answers = session.get("answers", {})
    lead_id = session.get("lead_id")
    import io
    nome = (lead.get("empresa") or "estrategia").replace(" ", "_")

    # Reaproveita o PDF ja gerado nesta sessao: re-downloads entregam o mesmo
    # relatorio, sem gerar uma analise diferente a cada clique.
    cached = _REPORT_CACHE.get(lead_id)
    if cached:
        return send_file(io.BytesIO(cached), mimetype="application/pdf",
                         as_attachment=True,
                         download_name=f"Estrategia_Marketing_{nome}.pdf")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        return ("<h2>Relatório indisponível</h2><p>A chave da API da Anthropic "
                "(ANTHROPIC_API_KEY) não foi configurada. As respostas já foram salvas. "
                "Defina a chave e reinicie o app para gerar o PDF.</p>"), 503

    # Serializa a geracao por lead: se outra requisicao ja esta gerando este
    # relatorio, esta aqui espera no lock e, ao entrar, encontra o cache pronto.
    with _lead_lock(lead_id):
        pdf = _REPORT_CACHE.get(lead_id)
        if pdf is None:
            try:
                analysis = report.analyze(lead, answers)
                pdf = report.build_pdf(lead, analysis)
            except Exception as e:
                return jsonify({"erro": f"Falha ao gerar a análise: {e}"}), 500
            _REPORT_CACHE[lead_id] = pdf
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
