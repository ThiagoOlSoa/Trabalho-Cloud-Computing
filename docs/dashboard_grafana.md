# Observatório de Evasão e Retenção no Grafana

O Grafana consulta `public.vw_observatorio_censo_enade` por uma fonte PostgreSQL de leitura. A view fornece uma linha por curso do Censo 2024 nas dimensões 1 e 2, com ENADE 2023 associado pelo código de curso. O GitHub versiona o JSON, o gerador e o SQL. A instância Grafana guarda os parâmetros da conexão. O painel usa agregados, sem série temporal, e roda sem o Streamlit.

## Painéis e resultados de referência

| Painel ou medida | Fórmula ou conteúdo | Sem filtros restritivos | Consulta em `grafana/queries/` |
|---|---|---:|---|
| Cursos | Contagem de linhas da view | 7.078 | `indicadores.sql` |
| Matrículas | Soma de `qt_mat` | 1.269.093 | `indicadores.sql` |
| Participação feminina | Soma de matrículas femininas ÷ soma de matrículas | 20,2% | `indicadores.sql` |
| Participação preta/parda | Soma de matrículas pretas e pardas ÷ soma de matrículas com raça/cor declarada | 41,2% | `indicadores.sql` |
| Desvinculação anual | Soma de desvinculados ÷ soma de matrículas, trancados, desvinculados, transferidos e falecidos | 21,7% | `indicadores.sql` |
| Média geral ENADE | Média das notas de curso entre 0 e 100, ponderada pelo número positivo de notas válidas | 41,8 | `indicadores.sql` |
| Ingressantes | Soma de `qt_ing` | 673.375 | `indicadores.sql` |
| Concluintes | Soma de `qt_conc` | 153.760 | `indicadores.sql` |
| Cursos com ENADE e cobertura | Contagem de correspondências e proporção entre os cursos do recorte | 1.665 · 23,5% | `indicadores.sql` |
| Comparações por grau e modalidade | Participação feminina e preta/parda, cada uma calculada sobre o seu denominador em cada grupo | — | `comparacoes.sql` |
| Populações observadas | Totais e composição feminina e preta/parda de ingressantes, matriculados e concluintes | — | `populacoes.sql` |
| Qualidade da declaração | Censo usa `CORND` sobre matrículas. ENADE usa não declaração ou sem resposta sobre participantes | — | `declaracao.sql` |
| Perfis agregados | Modalidade e faixas de composição feminina (<10%, 10–20%, >20%) e preta/parda (<25%, 25–50%, >50%) para cursos com ≥30 matrículas | — | `perfis.sql` |

Os percentuais são razões de somas. Um zero conhecido permanece zero. Uma soma obrigatória com lacunas ou um denominador sem base válida resulta em valor indisponível. Cobertura ENADE mede correspondência de curso mesmo sem notas válidas. Os percentuais de composição descrevem populações observadas no respectivo ano. Taxas longitudinais exigem dados de coorte, e medidas sobre mulheres negras exigem o cruzamento individual de sexo e raça/cor. [Contrato analítico da Etapa 5A](indicadores.md)

## Recorte e limites operacionais

As cinco listas com multisseleção são grau, modalidade, rede, UF de oferta e área Cine. ENADE é uma seleção única entre todos os cursos e apenas os que têm registro em 2023. As listas são carregadas a partir da view e usam o mesmo recorte normalizado dos painéis. Nos filtros com `= ANY(ARRAY[...]::text[])` e na condição ENADE, o formato `:sqlstring` delimita literais e escapa aspas simples. **All** expande os valores da lista, sem expressão SQL configurável. Todas as consultas são `SELECT`. O papel PostgreSQL de leitura é a barreira de permissão da fonte.

A UF identifica a oferta **presencial** no Censo. Quando a view pode atribuir uma UF a partir do ENADE por divergência de modalidade, o painel usa **UF indisponível** para o curso presencial. EaD recebe **EaD · UF não atribuída**, inclusive quando o ENADE tem UF. Escolher uma UF presencial exclui os cursos EaD, a menos que a categoria EaD também seja selecionada. A área Cine segue o rótulo da view usado na Etapa 5A.

Os painéis retornam cartões, pequenas tabelas e séries categóricas agregadas, sem atualização periódica. As variáveis fazem cinco consultas ao abrir o dashboard. Cada alteração de filtros consulta novamente os painéis. A configuração de conexões reduz consultas simultâneas ao Free, que tem 1 GB de RAM, 1 CPU e 1 GB de armazenamento segundo a documentação. A latência e o impacto com vários espectadores dependem da instância e devem ser medidos após autorização. [Aiven PostgreSQL Free](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier)

Para importação, rede, TLS e compartilhamento, siga o [manual do Grafana](../grafana/README.md).

## Validação local

O dashboard foi importado no Grafana OSS 12.3.6 e executado no PostgreSQL 16.2 descartável com as bases completas. A renderização em navegador foi verificada como Viewer em 1.440 px e 390 px. Os dez indicadores de referência coincidiram. O filtro ENADE exibiu cobertura de 100% ao selecionar apenas cursos com registro, e a combinação presencial com a categoria geográfica EaD produziu uma seleção vazia. As capturas usam dados agregados do ensaio local. [Desktop](img/grafana-desktop.png) · [Mobile e filtros](img/grafana-mobile.png) · [Mobile e gráficos](img/grafana-mobile-graficos.png)
