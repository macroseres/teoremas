# Índice de teoremas

Coleção de teoremas de matemática de graduação, organizada por área. Cada página traz o enunciado, a ideia da prova, a demonstração, um exemplo, uma advertência sobre as hipóteses (com contraexemplo) e um complemento. As fórmulas são MathML pré-renderizado: não há JavaScript nem conexão externa.

- **Leitura online:** <https://macroseres.github.io/teoremas/>
- **Autor:** Edwin López
- **Licença:** [CC BY 4.0](LICENSE.md): copie e adapte, citando a autoria.
- **Como citar a coleção:** veja [`CITATION.cff`](CITATION.cff). Cada página também traz a sua própria citação no rodapé.

## Como o projeto é organizado

| Arquivo | Para que serve |
|---|---|
| `catalogo.csv` | **Registro central**: um teorema por linha (id, área, título, arquivo, resumo, palavras-chave, status, datas). Tudo o mais é gerado a partir dele. |
| `areas.csv` | As áreas e as referências bibliográficas de cada uma. |
| `ferramentas/publicar.py` | Atualiza metadados, licença, citação, navegação, índice, `sitemap.xml` e `robots.txt`, e valida tudo. |
| `ferramentas/novo.py` | Cria a página de um novo teorema a partir de um arquivo de texto (`novos/MODELO.txt`). |
| `auditoria.csv`, `REVISAO.txt` | Registro da revisão matemática. |

Para adicionar teoremas, leia [`COMO-ADICIONAR.md`](COMO-ADICIONAR.md).
