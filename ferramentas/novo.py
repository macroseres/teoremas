#!/usr/bin/env python3
"""Cria a página HTML de um novo teorema a partir de um arquivo de texto simples.

Uso (na pasta do projeto):
    python ferramentas/novo.py novos/meu-teorema.txt

O arquivo de texto segue o modelo de novos/MODELO.txt: um cabeçalho "chave: valor"
e seções "## Enunciado", "## Demonstração" etc. Fórmulas em TeX entre $...$
(na linha) ou $$...$$ (em destaque). Linhas em branco separam parágrafos; **negrito**
e *itálico* são aceitos.

O script: converte as fórmulas em MathML (sem JavaScript), monta a página com o mesmo
visual das demais, registra o teorema em catalogo.csv (status "rascunho"), acrescenta
uma linha em auditoria.csv e roda publicar.py. Para publicar de verdade, depois de
revisar, troque o status para "publicado" em catalogo.csv e rode publicar.py.
"""
import csv
import html
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import publicar  # noqa: E402
from tex2mml import render  # noqa: E402

RAIZ = publicar.RAIZ
SECOES = [  # (chave, título exibido, sufixo do id, classe CSS)
    ("enunciado", "Enunciado", "enunciado", "statement"),
    ("ideia", "Ideia da prova", "ideia", ""),
    ("demonstracao", "Demonstração", "demonstracao", ""),
    ("exemplo", "Exemplo", "exemplo", ""),
    ("atencao", "Atenção", "atencao", "note"),
    ("complemento", "Complemento", "complemento", ""),
]
OBRIGATORIAS = {"enunciado", "demonstracao"}


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn")


def slugificar(s):
    s = re.sub(r"[^a-z0-9]+", "-", sem_acento(re.sub(r"\$.*?\$", "", s))).strip("-")
    return s


def inline(texto):
    """Escapa HTML fora das fórmulas e aplica **negrito** / *itálico*."""
    partes = re.split(r"(\$\$.+?\$\$|\$.+?\$)", texto, flags=re.S)
    saida = []
    for i, p in enumerate(partes):
        if i % 2 == 1:
            saida.append(p)
            continue
        p = html.escape(p, quote=False)
        p = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", p)
        saida.append(p)
    return "".join(saida)


def corpo_secao(texto):
    paragrafos = [p.strip() for p in re.split(r"\n\s*\n", texto.strip()) if p.strip()]
    return render("".join(f"<p>{inline(' '.join(p.split(chr(10))))}</p>" for p in paragrafos))


def ler_fonte(caminho):
    bruto = Path(caminho).read_text(encoding="utf-8-sig")
    cab, _, resto = bruto.partition("\n## ")
    meta = {}
    for linha in cab.splitlines():
        if ":" in linha and not linha.startswith("#"):
            k, v = linha.split(":", 1)
            meta[sem_acento(k.strip()).replace(" ", "_").replace("-", "_")] = v.strip()
    secoes = {}
    if resto:
        for bloco in ("## " + resto).split("\n## "):
            bloco = bloco[3:] if bloco.startswith("## ") else bloco
            nome, _, texto = bloco.partition("\n")
            secoes[sem_acento(nome.strip()).replace(" da prova", "").replace(" ", "_")] = texto
    return meta, secoes


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    meta, secoes = ler_fonte(sys.argv[1])
    if "pre_requisitos" in meta:
        meta.setdefault("prerequisitos", meta["pre_requisitos"])
    for c in ("area", "titulo", "resumo", "prerequisitos"):
        if not meta.get(c):
            print(f"ERRO: falta o campo '{c}:' no cabeçalho.")
            return 1
    faltam = [s for s in OBRIGATORIAS if not secoes.get(s, "").strip()]
    if faltam:
        print("ERRO: faltam as seções:", ", ".join(faltam))
        return 1
    areas = {a["id"]: a for a in publicar.ler_areas()}
    if meta["area"] not in areas:
        print("ERRO: área desconhecida. Use uma destas:", ", ".join(areas))
        return 1
    area = areas[meta["area"]]
    catalogo = publicar.ler_catalogo()
    slug = meta.get("arquivo") or f"{area['id']}-{slugificar(meta['titulo'])}"
    slug = re.sub(r"\.html$", "", slug)
    arquivo = slug + ".html"
    if any(r["arquivo"] == arquivo for r in catalogo) or (RAIZ / arquivo).exists():
        print(f"ERRO: {arquivo} já existe.")
        return 1
    novo_id = f"{max(int(r['id']) for r in catalogo) + 1:05d}"
    status = "publicado" if meta.get("status", "").lower() == "publicado" else "rascunho"
    hoje = date.today().isoformat()

    # modelo visual: uma página existente da mesma área (ou qualquer uma)
    modelos = [r for r in catalogo if r["area_id"] == area["id"]] or catalogo
    t0 = (RAIZ / modelos[0]["arquivo"]).read_text(encoding="utf-8")
    prefixo = t0[: t0.index("<main>")]
    sufixo = t0[t0.index("</main>"):]

    titulo_html = publicar.texto_para_html(meta["titulo"])
    resumo_html = publicar.texto_para_html(meta["resumo"])
    toc, secs = [], []
    for chave, rotulo, suf, classe in SECOES:
        texto = secoes.get(chave, "").strip()
        if not texto:
            continue
        sid = f"{slug}-{suf}"
        toc.append(f'<li><a href="#{sid}">{rotulo}</a></li>')
        secs.append(f'<section id="{sid}" class="{classe}"><h2>{rotulo}</h2>{corpo_secao(texto)}</section>')
    rid = f"{slug}-referencia"
    refs = meta.get("referencias") or area["referencias"]
    toc.append(f'<li><a href="#{rid}">Referências da área</a></li>')
    secs.append(f'<section id="{rid}" class="reference"><h2>Referências da área</h2>'
                f'<p>{html.escape(refs, quote=False)}</p></section>')
    pre_html = render(f"<p>{inline(meta['prerequisitos'])}</p>")[3:-4]
    corpo = (f'<main><article class="frame" id="{slug}"><div class="article-hero">'
             f'<p class="tag">{html.escape(area["nome"])} · {novo_id}</p><h1>{titulo_html}</h1>'
             f'<p class="lead">{resumo_html}</p></div><div class="reading">'
             f'<nav class="toc" aria-label="Nesta demonstração"><strong>Nesta página</strong><ul>{"".join(toc)}</ul></nav>'
             f'<div class="body"><p class="prereq"><strong>Pré-requisitos:</strong> {pre_html}</p>{"".join(secs)}</div></div>'
             f'</article>')
    (RAIZ / arquivo).write_text(prefixo + corpo + sufixo, encoding="utf-8", newline="")

    chaves = meta.get("palavras_chave") or f"teorema; demonstração; {area['nome'].lower()}"
    with open(RAIZ / "catalogo.csv", "a", encoding="utf-8", newline="") as f:
        csv.writer(f, delimiter=";", lineterminator="\r\n").writerow(
            [novo_id, area["nome"], meta["titulo"], arquivo, area["id"], meta["resumo"], chaves,
             status, hoje, hoje])
    aud = RAIZ / "auditoria.csv"
    if aud.exists():
        with open(aud, "a", encoding="utf-8", newline="") as f:
            csv.writer(f, delimiter=";", lineterminator="\r\n").writerow(
                [novo_id, area["nome"], meta["titulo"], arquivo, "PENDENTE",
                 "Novo teorema: revisar enunciado, hipóteses, demonstração e exemplos antes de publicar."])
    print(f"Criado {arquivo} (id {novo_id}, status {status}).")
    sys.argv = ["publicar.py"]
    return publicar.main()


if __name__ == "__main__":
    sys.exit(main())
