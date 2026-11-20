#!/usr/bin/env python3
"""Teoremas em prova - publicação e manutenção da coleção.

Uso (na pasta do projeto):
    python ferramentas/publicar.py            # aplica tudo e valida
    python ferramentas/publicar.py --verificar  # só valida, não escreve nada

O catálogo (catalogo.csv) é a fonte única de verdade. Este script lê o
catálogo e, de forma idempotente (pode rodar quantas vezes quiser):

  1. atualiza em cada página publicada: metadados (descrição, URL canônica,
     Open Graph, JSON-LD, citação), licença, "como citar", rodapé e a
     navegação anterior/próximo dentro da área;
  2. regenera o índice (index.html): lista por área, contagens e filtro;
  3. gera sitemap.xml e robots.txt;
  4. valida: arquivos existentes, ids únicos, títulos e resumos coerentes,
     MathML bem formado, âncoras do sumário e links.

Só usa a biblioteca padrão do Python 3.8+.
"""
import csv
import html
import json
import re
import sys
from pathlib import Path
from xml.dom import minidom

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tex2mml import span as _span  # noqa: E402  (TeX -> MathML)

RAIZ = Path(__file__).resolve().parent.parent
CFG = json.loads((RAIZ / "ferramentas" / "config.json").read_text(encoding="utf-8"))
BASE = CFG["base_url"].rstrip("/") + "/"
EXTENSO = {1: "uma", 2: "duas", 3: "três", 4: "quatro", 5: "cinco", 6: "seis", 7: "sete",
           8: "oito", 9: "nove", 10: "dez", 11: "onze", 12: "doze", 13: "treze", 14: "quatorze",
           15: "quinze", 16: "dezesseis", 17: "dezessete", 18: "dezoito", 19: "dezenove", 20: "vinte"}
COLUNAS = ["id", "area", "titulo", "arquivo", "area_id", "resumo", "palavras_chave",
           "status", "registrado", "modificado"]


def esc(s):
    return html.escape(s, quote=True)


def plano(s):
    """Texto sem os marcadores $...$ (para <title>, meta, citação)."""
    return s.replace("$", "")


def texto_para_html(s):
    """Texto com $tex$ -> HTML com MathML pré-renderizado."""
    partes = re.split(r"\$(.+?)\$", s)
    return "".join(html.escape(p, quote=False) if i % 2 == 0 else _span(p, False)
                   for i, p in enumerate(partes))


def html_para_texto(fragmento):
    """HTML de uma página -> texto com $tex$ nas fórmulas (inverso do anterior)."""
    f = re.sub(r"<span class=\"katex\"><math.*?<annotation[^>]*>(.*?)</annotation>.*?</math></span>",
               lambda m: "$" + html.unescape(m.group(1)) + "$", fragmento, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", f)).strip()


def ler_csv(nome):
    with open(RAIZ / nome, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def ler_catalogo():
    linhas = ler_csv("catalogo.csv")
    for r in linhas:
        r["status"] = (r.get("status") or "rascunho").strip().lower()
    return sorted(linhas, key=lambda r: int(r["id"]))


def ler_areas():
    return ler_csv("areas.csv")


def url(arquivo):
    return BASE if arquivo == "index.html" else BASE + arquivo


def plural(n, um, varios):
    return f"{n} {um if n == 1 else varios}"


# ---------------------------------------------------------------- blocos de página
CSS_PUB = ("<style>.site-foot p{margin:.3rem 0}.site-foot .cite{overflow-wrap:anywhere}"
           ".site-foot .lic{font-size:.88rem}</style>")


def bloco_head(titulo, resumo, arquivo, chaves, registrado, modificado, indice=False):
    u = url(arquivo)
    autor = CFG["autor"]
    site = CFG["site"]
    ld_autor = {"@type": "Person", "name": autor}
    if indice:
        ld = {"@context": "https://schema.org", "@type": "CollectionPage", "name": titulo,
              "description": resumo, "url": u, "inLanguage": "pt-BR", "author": ld_autor,
              "license": CFG["licenca_url"]}
    else:
        ld = {"@context": "https://schema.org", "@type": "LearningResource", "name": titulo,
              "headline": titulo, "description": resumo, "url": u, "inLanguage": "pt-BR",
              "author": ld_autor, "license": CFG["licenca_url"],
              "educationalLevel": "Graduação", "learningResourceType": "Teorema com demonstração",
              "keywords": chaves, "datePublished": registrado, "dateModified": modificado,
              "isPartOf": {"@type": "WebSite", "name": site, "url": BASE}}
    partes = [
        '<meta name="robots" content="index, follow">',
        f'<meta name="description" content="{esc(resumo)}">',
        f'<meta name="author" content="{esc(autor)}">',
        f'<link rel="canonical" href="{esc(u)}">',
        f'<link rel="license" href="{esc(CFG["licenca_url"])}">',
        '<meta name="theme-color" content="#122a35">',
        f'<meta property="og:site_name" content="{esc(site)}">',
        '<meta property="og:locale" content="pt_BR">',
        f'<meta property="og:type" content="{"website" if indice else "article"}">',
        f'<meta property="og:title" content="{esc(titulo)}">',
        f'<meta property="og:description" content="{esc(resumo)}">',
        f'<meta property="og:url" content="{esc(u)}">',
        '<meta name="twitter:card" content="summary">',
    ]
    if not indice:
        partes += [
            f'<meta name="citation_title" content="{esc(titulo)}">',
            f'<meta name="citation_author" content="{esc(autor)}">',
            f'<meta name="citation_publication_date" content="{esc(registrado.replace("-", "/"))}">',
            '<meta name="citation_language" content="pt">',
            f'<meta name="citation_public_url" content="{esc(u)}">',
        ]
    partes.append('<script type="application/ld+json">'
                  + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>")
    partes.append(CSS_PUB)
    return "<!--pub:head-->" + "".join(partes) + "<!--/pub:head-->"


def bloco_rodape(titulo, arquivo, registrado, indice=False):
    ano = registrado[:4]
    lic = (f'<p class="lic">© {ano} {esc(CFG["autor"])}. Texto e figuras sob licença '
           f'<a rel="license" href="{esc(CFG["licenca_url"])}">{esc(CFG["licenca_nome"])}</a>: '
           'você pode copiar e adaptar, desde que cite a autoria.</p>')
    if indice:
        return f'<!--pub:foot-->{lic}<!--/pub:foot-->'
    u = url(arquivo)
    cita = (f'<p class="cite"><strong>Como citar:</strong> {esc(CFG["autor_abnt"])}. '
            f'<em>{esc(titulo)}</em>. In: {esc(CFG["site"])}. '
            f'{ano}. Disponível em: <a href="{esc(u)}">{esc(u)}</a>.</p>')
    return f"<!--pub:foot-->{cita}{lic}<!--/pub:foot-->"


def aplicar_head(texto, bloco):
    texto = re.sub(r'<meta name="robots"[^>]*>', "", texto)
    texto = re.sub(r"<!--pub:head-->.*?<!--/pub:head-->", "", texto, flags=re.S)
    return texto.replace("</head>", bloco + "</head>", 1)


def aplicar_rodape(texto, bloco):
    novo, n = re.subn(r'<footer class="site-foot frame">.*?</footer>',
                      lambda m: '<footer class="site-foot frame">' + bloco + "</footer>",
                      texto, count=1, flags=re.S)
    if n != 1:
        raise ValueError("rodapé não encontrado")
    return novo


def nav_area(vizinhos, i):
    links = []
    if i > 0:
        a = vizinhos[i - 1]
        links.append(f'<a href="{esc(a["arquivo"])}"><small>Anterior na área</small>{texto_para_html(a["titulo"])}</a>')
    if i < len(vizinhos) - 1:
        p = vizinhos[i + 1]
        links.append(f'<a href="{esc(p["arquivo"])}"><small>Próximo na área</small>{texto_para_html(p["titulo"])}</a>')
    return ('<nav class="article-nav" aria-label="Mais teoremas desta área">'
            + "".join(links) + "</nav>")


def processar_pagina(r, vizinhos, i):
    caminho = RAIZ / r["arquivo"]
    t = caminho.read_text(encoding="utf-8")
    original = t
    publicado = r["status"] == "publicado"
    t = re.sub(r"<title>.*?</title>",
               lambda m: f"<title>{esc(plano(r['titulo']))} | {esc(CFG['site'])}</title>", t, count=1, flags=re.S)
    t = re.sub(r'<p class="tag">.*?</p>',
               lambda m: f'<p class="tag">{esc(r["area"])} · {r["id"]}</p>', t, count=1)
    t = re.sub(r'<nav class="article-nav".*?</nav>',
               lambda m: nav_area(vizinhos, i), t, count=1, flags=re.S)
    bloco = bloco_head(plano(r["titulo"]), plano(r["resumo"]), r["arquivo"], r["palavras_chave"],
                       r["registrado"], r["modificado"])
    if not publicado:
        bloco = bloco.replace('content="index, follow"', 'content="noindex, nofollow"', 1)
    t = aplicar_head(t, bloco)
    t = aplicar_rodape(t, bloco_rodape(plano(r["titulo"]), r["arquivo"], r["registrado"]))
    return caminho, original, t


# ---------------------------------------------------------------- índice
def gerar_indice(catalogo, areas):
    pub = [r for r in catalogo if r["status"] == "publicado"]
    secoes = []
    opcoes = ['<option value="">Todas as áreas</option>']
    usadas = 0
    for a in areas:
        itens = [r for r in pub if r["area_id"] == a["id"]]
        if not itens:
            continue
        usadas += 1
        lis = "".join(
            f'<li><a href="{esc(r["arquivo"])}"><small>{r["id"]} · {esc(r["area"])}</small>'
            f'<strong>{texto_para_html(r["titulo"])}</strong><span>{texto_para_html(r["resumo"])}</span></a></li>'
            for r in itens)
        secoes.append(f'<section class="catalog-area" id="{a["id"]}"><h3>{esc(a["nome"])} '
                      f'<small>{plural(len(itens), "teorema", "teoremas")}</small></h3>'
                      f'<ul class="catalog">{lis}</ul></section>')
        opcoes.append(f'<option value="{a["id"]}">{esc(a["nome"])}</option>')
    return pub, usadas, '<nav aria-label="Índice por área">' + "".join(secoes) + "</nav>", "".join(opcoes)


def processar_indice(catalogo, areas):
    caminho = RAIZ / "index.html"
    t = caminho.read_text(encoding="utf-8")
    original = t
    pub, usadas, nav, opcoes = gerar_indice(catalogo, areas)
    n = len(pub)
    t, k = re.subn(r'<nav aria-label="Índice por área">.*?</nav>', lambda m: nav, t, count=1, flags=re.S)
    assert k == 1, "nav do índice não encontrado"
    t, k = re.subn(r'(<select id="area"[^>]*>).*?(</select>)',
                   lambda m: m.group(1) + opcoes + m.group(2), t, count=1, flags=re.S)
    assert k == 1, "select de áreas não encontrado"
    t = re.sub(r'(<p id="filter-count"[^>]*>)[^<]*(</p>)',
               lambda m: m.group(1) + plural(n, "teorema", "teoremas") + m.group(2), t, count=1)
    ext = EXTENSO.get(usadas, str(usadas))
    t = re.sub(r'(<p class="lead">)[^<]*(</p><a class="hero-link")',
               lambda m: (f'{m.group(1)}{n} teoremas em {ext} áreas da matemática. Cada página expõe as '
                          f'hipóteses, desenvolve a demonstração e mostra exemplos e contraexemplos.'
                          f'{m.group(2)}'), t, count=1)
    resumo = (f"Coleção de {n} teoremas de matemática de graduação, com hipóteses, demonstração, "
              "exemplos e contraexemplos.")
    t = re.sub(r"<title>.*?</title>", f"<title>{esc(CFG['site'])} | Índice</title>", t, count=1, flags=re.S)
    hoje = max(r["modificado"] for r in pub) if pub else ""
    t = aplicar_head(t, bloco_head(CFG["site"], resumo, "index.html", "", hoje, hoje, indice=True))
    t = aplicar_rodape(t, bloco_rodape(CFG["site"], "index.html", hoje or "2026", indice=True))
    return caminho, original, t


# ---------------------------------------------------------------- sitemap e robots
def gerar_sitemap(catalogo):
    pub = [r for r in catalogo if r["status"] == "publicado"]
    ultimo = max((r["modificado"] for r in pub), default="")
    linhas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
              f"<url><loc>{esc(BASE)}</loc><lastmod>{ultimo}</lastmod></url>"]
    for r in pub:
        linhas.append(f"<url><loc>{esc(url(r['arquivo']))}</loc><lastmod>{r['modificado']}</lastmod></url>")
    linhas.append("</urlset>")
    return "\n".join(linhas) + "\n"


def gerar_robots():
    return f"User-agent: *\nAllow: /\n\nSitemap: {BASE}sitemap.xml\n"


# ---------------------------------------------------------------- validação
def texto_tag(t, padrao):
    m = re.search(padrao, t, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else None


def validar(catalogo, areas):
    erros, avisos = [], []
    ids, arqs = set(), set()
    ids_area = {a["id"] for a in areas}
    nome_area = {a["id"]: a["nome"] for a in areas}
    for r in catalogo:
        for c in COLUNAS:
            if not (r.get(c) or "").strip():
                erros.append(f"{r.get('arquivo')}: coluna '{c}' vazia no catálogo")
        if r["id"] in ids:
            erros.append(f"id repetido: {r['id']}")
        ids.add(r["id"])
        if r["arquivo"] in arqs:
            erros.append(f"arquivo repetido: {r['arquivo']}")
        arqs.add(r["arquivo"])
        if r["area_id"] not in ids_area:
            erros.append(f"{r['arquivo']}: area_id desconhecido '{r['area_id']}'")
        elif nome_area[r["area_id"]] != r["area"]:
            erros.append(f"{r['arquivo']}: nome da área difere de areas.csv")
        p = RAIZ / r["arquivo"]
        if not p.exists():
            erros.append(f"{r['arquivo']}: arquivo não existe")
            continue
        t = p.read_text(encoding="utf-8")
        m1 = re.search(r"<h1>(.*?)</h1>", t, flags=re.S)
        h1 = html_para_texto(m1.group(1)) if m1 else None
        if h1 != r["titulo"]:
            erros.append(f"{r['arquivo']}: título do catálogo difere do <h1> ('{h1}')")
        m2 = re.search(r'<p class="lead">(.*?)</p>', t, flags=re.S)
        lead = html_para_texto(m2.group(1)) if m2 else None
        if lead != r["resumo"]:
            erros.append(f"{r['arquivo']}: resumo do catálogo difere do texto da página")
        for m in re.findall(r"<math.*?</math>", t, flags=re.S):
            try:
                minidom.parseString(m)
            except Exception as e:  # noqa: BLE001
                erros.append(f"{r['arquivo']}: MathML inválido ({e})")
                break
        alvos = set(re.findall(r'\bid="([^"]+)"', t))
        for ancora in re.findall(r'<a href="#([^"]+)"', t):
            if ancora not in alvos:
                erros.append(f"{r['arquivo']}: âncora #{ancora} sem destino")
        if r["status"] == "publicado" and "noindex" in t:
            erros.append(f"{r['arquivo']}: publicado mas ainda com noindex (rode publicar.py)")
    nos_catalogo = {r["arquivo"] for r in catalogo}
    for p in sorted(RAIZ.glob("*.html")):
        if p.name not in nos_catalogo and p.name not in ("index.html", "404.html"):
            avisos.append(f"{p.name}: página HTML fora do catálogo (não entra no índice nem no sitemap)")
    return erros, avisos


# ---------------------------------------------------------------- principal
def main():
    so_verificar = "--verificar" in sys.argv
    catalogo = ler_catalogo()
    areas = ler_areas()
    por_area = {}
    for r in catalogo:
        if r["status"] == "publicado":
            por_area.setdefault(r["area_id"], []).append(r)
    alteracoes = []
    for r in catalogo:
        viz = por_area.get(r["area_id"], [])
        i = viz.index(r) if r in viz else 0
        if not (RAIZ / r["arquivo"]).exists():
            continue
        alteracoes.append(processar_pagina(r, viz or [r], i))
    alteracoes.append(processar_indice(catalogo, areas))
    extras = [(RAIZ / "sitemap.xml", gerar_sitemap(catalogo)), (RAIZ / "robots.txt", gerar_robots())]
    mudou = 0
    if not so_verificar:
        for caminho, antes, depois in alteracoes:
            if antes != depois:
                caminho.write_text(depois, encoding="utf-8", newline="")
                mudou += 1
        for caminho, conteudo in extras:
            atual = caminho.read_text(encoding="utf-8") if caminho.exists() else None
            if atual != conteudo:
                caminho.write_text(conteudo, encoding="utf-8", newline="")
                mudou += 1
    erros, avisos = validar(catalogo, areas)
    pub = sum(1 for r in catalogo if r["status"] == "publicado")
    print(f"{len(catalogo)} teoremas no catálogo ({pub} publicados, {len(catalogo) - pub} rascunhos).")
    if not so_verificar:
        print(f"{mudou} arquivo(s) atualizado(s).")
    for a in avisos:
        print("AVISO:", a)
    for e in erros:
        print("ERRO:", e)
    print("Tudo certo." if not erros else f"{len(erros)} erro(s).")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
