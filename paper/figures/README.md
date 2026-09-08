# Figuras como PDF autônomo

Todas as figuras do artigo são TikZ, desenhadas dentro do fonte a partir dos JSON medidos.
Isso mantém cada número rastreável, mas cria um risco de submissão: **um sistema editorial
que não compile o fonte não tem arquivo de imagem para receber.**

Estes seis PDFs cobrem esse caso. Cada um foi extraído do mesmo `tikzpicture` que o artigo
usa, com o mesmo preâmbulo, e compilado em `standalone`:

| arquivo | onde aparece |
|---|---|
| `fig_overview.pdf` | Figura 1 do corpo |
| `fig_jusante.pdf` | Figura 2 do corpo |
| `fig_mecanismo.pdf` | Figura S1 |
| `fig_direcao.pdf` | Figura S2 |
| `fig_menu.pdf` | Figura S3 |
| `fig_inversao.pdf` | Figura S4 |

⚠️ **Estes arquivos são derivados, não fonte.** Quem mudar uma figura mexe no
`gera_fig_*.py`, e estes PDFs precisam ser regerados. O artigo continua compilando sem eles.
