# Observatório de Evasão e Retenção no Grafana

O Grafana consulta as tabelas do PostgreSQL por uma fonte de leitura. A [CTE compartilhada](../grafana/queries/cursos.sql) fornece uma linha por curso do Censo 2024 nas dimensões 1 e 2 e associa o ENADE 2023 por código de curso. O dashboard dispensa objetos novos na Aiven. O GitHub versiona o JSON, o gerador e o SQL. A instância Grafana guarda os parâmetros da conexão. O painel usa agregados, sem série temporal, e roda sem o Streamlit.

## Painéis e resultados de referência

| Painel ou medida | Fórmula ou conteúdo | Sem filtros restritivos | Consulta em `grafana/queries/` |
|---|---|---:|---|
| Cursos | Contagem de linhas no recorte por curso | 7.078 | `indicadores.sql` |
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

As cinco listas com multisseleção são grau, modalidade, rede, UF de oferta e área Cine. ENADE é uma seleção única entre todos os cursos e apenas os que têm registro em 2023. As listas são carregadas a partir das tabelas e usam o mesmo recorte normalizado dos painéis. Nos filtros com `= ANY(ARRAY[...]::text[])` e na condição ENADE, o formato `:sqlstring` delimita literais e escapa aspas simples. **All** expande os valores da lista, sem expressão SQL configurável. Todas as consultas são `SELECT`. O papel PostgreSQL de leitura é a barreira de permissão da fonte.

A UF identifica a oferta **presencial** no Censo. Quando a modalidade do ENADE diverge do Censo e o curso é presencial no Censo, o painel usa **UF indisponível** para o curso presencial. EaD recebe **EaD · UF não atribuída**, inclusive quando o ENADE tem UF. Escolher uma UF presencial exclui os cursos EaD, a menos que a categoria EaD também seja selecionada. A área Cine segue o rótulo usado na Etapa 5A.

Os painéis retornam cartões, pequenas tabelas e séries categóricas agregadas, sem atualização periódica. As variáveis fazem cinco consultas ao abrir o dashboard. Cada alteração de filtros consulta novamente os painéis. A configuração de conexões reduz consultas simultâneas ao Free, que tem 1 GB de RAM, 1 CPU e 1 GB de armazenamento segundo a documentação. A latência e o impacto com vários espectadores dependem da instância e devem ser medidos após autorização. [Aiven PostgreSQL Free](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier)

Para importação, rede, TLS e compartilhamento, siga o [manual do Grafana](../grafana/README.md).

## Validação visual da Etapa 7A

O dashboard foi importado no Grafana OSS 12.3.6 e executado no PostgreSQL 16.2 descartável com as bases completas. A renderização em navegador foi verificada como Viewer em 1.440 px e 390 px. Os dez indicadores de referência coincidiram. O filtro ENADE exibiu cobertura de 100% ao selecionar apenas cursos com registro, e a combinação presencial com a categoria geográfica EaD produziu uma seleção vazia. As capturas usam dados agregados do ensaio local. [Desktop](img/grafana-desktop.png) · [Mobile e filtros](img/grafana-mobile.png) · [Mobile e gráficos](img/grafana-mobile-graficos.png)

## Compatibilidade com a Aiven — Etapa 7B

A equipe confirmou o banco `defaultdb`, o código Censo `INTEGER`, o código ENADE `VARCHAR` e 1.665 chaves ENADE válidas e distintas após normalização. O esquema de referência do repositório guiou a seleção das outras colunas. Seus nomes, tipos e privilégios no servidor real devem ser conferidos com o [preflight somente leitura](../grafana/preflight_aiven.sql). Tipos diferentes dos esperados precisam de revisão antes de conectar o Grafana.

O Censo é agregado antes da junção. O `LEFT JOIN` preserva os cursos sem ENADE. A normalização aceita espaços nas extremidades e zeros à esquerda, compara chaves como texto e evita converter chaves malformadas ou muito grandes em inteiros. A CTE materializada calcula a chave uma vez para cada registro de 2023 em cada consulta. O grão de uma linha por curso pressupõe chaves ENADE normalizadas únicas e as chaves das dimensões sem duplicatas. Se a conferência encontrar colisões, interrompa a configuração e investigue as variantes.

As listas de grau, modalidade, rede, UF e Cine são textuais. Os códigos de modalidade são inteiros. `possui_enade_2023` é booleano. A consulta aceita notas armazenadas em tipos numéricos, incluindo `double precision`, e as converte para `numeric` antes do cálculo ponderado. As fórmulas dos painéis, seus filtros, as cores e a organização da Etapa 7A foram preservados.

### Como reproduzir a validação local

1. Carregue os dois CSVs completos em um PostgreSQL descartável com `sql/schema.sql` e os loaders. Se a branch exigir CSV simples, descompacte os gzip em uma pasta temporária. Antes de instalar qualquer view, clone o banco com `createdb --template NOME_BASE NOME_LEGADO`.
2. Instale `sql/views.sql` no banco de referência da 7A. Somente na cópia descartável, execute `tests/fixtures/grafana_legado.sql`. A fixture reproduz o ENADE com chave `VARCHAR`, exercita um código com espaços e zeros à esquerda e testa `double precision` como variante para a nota geral. A view antiga simulada retorna apenas cursos associados. O banco de teste direto dispensa a V2.
3. No banco legado descartável, crie o papel de teste `grafana_direto` com login, sem privilégios administrativos e com `default_transaction_read_only=on`. Execute `tests/fixtures/grafana_permissoes.sql` nele. O papel precisa de `CONNECT` no banco.
4. Configure `ETL_TEST_PG_SOCKET`, `ETL_TEST_DB_NAME` para a referência, `GRAFANA_TEST_LEGACY_DB_NAME` para o legado e `GRAFANA_TEST_LEGACY_USER=grafana_direto`. Para paridade com CSV, configure `ETL_TEST_CSV_DIR`. Se necessário, configure `ETL_TEST_PSQL` e `ETL_TEST_PG_USER`. Execute `python -m unittest discover -s tests -v` e `python grafana/gerar_dashboard.py --check`.

### Resultado no PostgreSQL descartável

A suíte passou em 38 testes. Os dez indicadores, as opções dos seis filtros e os resultados de cartões, gráficos e tabelas coincidiram com a referência da 7A. O recorte teve 7.078 linhas e 7.078 cursos distintos, incluindo 5.413 cursos sem ENADE. O papel de teste leu as 42 colunas necessárias e os testes confirmaram que ele não podia inserir no fato Censo, ler a coluna não concedida `qt_mat_masc` ou consultar a view antiga.

Em uma execução serial por consulta no PostgreSQL 16.2 local, cinco consultas de listas e nove consultas de painéis levaram de 46 a 227 ms cada, com mediana de 99 ms, segundo `EXPLAIN ANALYZE`. Essas medidas excluem a latência de rede e a concorrência da Aiven.

### Pendências para conexão real

1. Após autorização para leitura, confirme o esquema no `defaultdb` com o preflight. Todas as colunas devem ter tipo aceito e as três contagens de chaves ENADE devem retornar 1.665. Confirme o grão das dimensões e compare os dez indicadores da tabela deste documento.
2. Após autorização do responsável pelo banco, confirme o papel dedicado, os privilégios por coluna e as permissões efetivas herdadas. Leitura direta concede acesso às colunas de origem. Revise esse alcance antes de dar acesso a usuários do Grafana. Repita o preflight com a conta de leitura.
3. Confirme DNS, porta, regras de rede e TLS `verify-full` com a CA da Aiven. Use **Save & test** e confira cartões, gráficos e filtros com um perfil Viewer. Meça o tempo de resposta na instância real antes de autorizar o deploy.
