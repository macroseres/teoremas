# Como adicionar novos teoremas

Requisito: Python 3.8 ou mais novo (só biblioteca padrão; nada a instalar).

## 1. Escreva o teorema em texto simples

Copie `novos/MODELO.txt` para `novos/meu-teorema.txt` e preencha. Fórmulas em TeX entre `$...$` (na linha) ou `$$...$$` (em destaque). As seções obrigatórias são **Enunciado** e **Demonstração**; **Ideia da prova**, **Exemplo**, **Atenção** e **Complemento** são opcionais.

## 2. Gere a página

```
python ferramentas/novo.py novos/meu-teorema.txt
```

O script converte as fórmulas, cria o HTML com o visual padrão, registra o teorema em `catalogo.csv` com status `rascunho` (a página fica com `noindex`, fora do índice e do sitemap) e acrescenta uma linha `PENDENTE` em `auditoria.csv`.

## 3. Revise e publique

1. Abra o HTML no navegador e confira o texto e as fórmulas.
2. Em `catalogo.csv`, troque o status de `rascunho` para `publicado` (e atualize a data em `modificado` sempre que alterar um teorema).
3. Rode `python ferramentas/publicar.py`. Ele atualiza o índice, a navegação anterior/próximo da área, o sitemap e valida tudo.
4. Em `auditoria.csv`, troque `PENDENTE` por `OK` depois da sua revisão matemática.
5. Faça o commit e o push; o GitHub Pages republica sozinho.

## Nova área

Acrescente uma linha em `areas.csv` (`id`, `nome`, `titulo_referencias`, `referencias`; o `id` é curto e sem acentos) e use esse `id` no campo `area:` do arquivo de texto.

## Corrigir um teorema existente

Edite o HTML (ou o título/resumo em `catalogo.csv`; os dois precisam coincidir, o `publicar.py` avisa se divergirem), atualize `modificado` e rode `python ferramentas/publicar.py`.

## O que o `publicar.py` valida

Ids e arquivos únicos; arquivo existente para cada linha do catálogo; título e resumo iguais aos da página; MathML bem formado; links do sumário com destino; nenhuma página publicada com `noindex`; páginas HTML fora do catálogo (aviso).
