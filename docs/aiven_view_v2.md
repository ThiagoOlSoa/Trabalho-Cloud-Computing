# View V2 candidata para a Aiven (etapa 6E)

Os arquivos foram adaptados do `sql/views.sql` consolidado, com duas diferenças: nome novo `vw_observatorio_censo_enade_v2` e associação ENADE–Censo por código de curso normalizado em texto (`co_curso` é VARCHAR na Aiven legado, INTEGER no Censo).

**Este diretório é somente uma proposta de migração.** Nenhum script foi executado na Aiven. A nova view não substitui a view original; quando criada, é um objeto adicional. O Grafana da equipe deve referenciar a V2 apenas depois de homologada.

1. Execute **somente** `aiven_v2_previa.sql` no PG Studio. É um SELECT com CTE que valida toda a definição proposta sem escrever. Resultado esperado: 7.078 linhas e 7.078 cursos distintos, 1.665 com ENADE e 5.413 sem ENADE, cobertura de 23,5%; 1.269.093 matrículas; 673.375 ingressantes; 153.760 concluintes; 20,2%, 41,2%, 21,7%, ENADE 41,8.
2. Em caso de erro de tipo, nome de coluna ou dados divergentes, pare e registre o erro. Inspecione os metadados do esquema e ajuste a proposta em ambiente descartável.
3. Somente **após autorização explícita do administrador do banco e resultados corretos da prévia**, execute `aiven_v2_criacao.sql` no PG Studio. Ele adiciona a nova view sem tocar nas tabelas ou view antiga. Se o nome já existir, falhará sem substituí-lo.
4. Execute `aiven_v2_validacao.sql` para conferir a nova view.
5. Confirme acesso com o usuário de leitura e análise das dependências antes de apontar Grafana para a V2. Não renomeie nem apague a view antiga sem uma migração planejada.

Nenhuma senha, URI ou token deve entrar no repositório. A aplicação Streamlit original não foi alterada.

## Revisão da proposta

A revisão 7B corrige o predicado SQL de normalização nas duas definições e adiciona a contagem de chaves distintas e a cobertura às consultas de conferência. A normalização compara texto, aceita espaços nas extremidades e zeros à esquerda e evita conversão numérica de códigos inválidos. A CTE materializada limita o ENADE à edição 2023 e calcula a chave uma vez por registro em cada consulta. O `LEFT JOIN` preserva cursos sem ENADE.

Uma chave VARCHAR única pode colidir após a normalização, por exemplo `123` e `00123`. Se o total de linhas superar os cursos distintos, interrompa a homologação. Localize os grupos com a consulta abaixo, avalie as variantes com o responsável e siga com uma correção revisada. A V2 preserva todos os registros de origem e não escolhe automaticamente uma linha entre variantes.

```sql
SELECT COALESCE(NULLIF(LTRIM(BTRIM(co_curso::text), '0'), ''), '0') AS co_curso_normalizado,
       COUNT(*) AS registros
FROM public.fato_enade_curso
WHERE nu_ano = 2023 AND BTRIM(co_curso::text) ~ '^[0-9]+$'
GROUP BY 1
HAVING COUNT(*) > 1;
```
