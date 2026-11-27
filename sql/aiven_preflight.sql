-- Etapa 6C: inventario somente leitura, seguro ate em banco vazio.
-- Pode ser executado no SQL Editor do PG Studio da Aiven.
-- Nao executa CREATE, INSERT, UPDATE, DELETE, ALTER ou DROP.
-- ATENCAO: nao compartilhe capturas que exponham nomes internos da conta.

BEGIN TRANSACTION READ ONLY;

SELECT current_database() AS banco,
       current_user AS usuario,
       current_setting('server_version') AS versao_pg,
       current_setting('search_path') AS caminho_de_esquemas,
       pg_database_size(current_database()) AS tamanho_total_bytes,
       pg_size_pretty(pg_database_size(current_database())) AS tamanho_total_banco;

SELECT to_regclass('public.dim_ies') AS dim_ies,
       to_regclass('public.dim_curso') AS dim_curso,
       to_regclass('public.dim_cine') AS dim_cine,
       to_regclass('public.dim_localizacao') AS dim_localizacao,
       to_regclass('public.fato_censo_curso') AS fato_censo,
       to_regclass('public.fato_enade_curso') AS fato_enade,
       to_regclass('public.vw_observatorio_censo_enade') AS view_integrada;

SELECT n.nspname AS esquema,
       c.relname AS objeto,
       CASE c.relkind WHEN 'r' THEN 'tabela'
                      WHEN 'v' THEN 'view'
                      WHEN 'm' THEN 'view materializada'
                      ELSE c.relkind::text END AS tipo,
       CASE WHEN c.relkind IN ('r','m')
            THEN pg_size_pretty(pg_total_relation_size(c.oid))
            ELSE NULL END AS armazenamento,
       stats.n_live_tup AS linhas_estimadas,
       has_schema_privilege(n.oid, 'USAGE') AS acesso_esquema,
       has_table_privilege(c.oid, 'SELECT') AS pode_ler,
       has_table_privilege(c.oid, 'INSERT') AS pode_inserir,
       has_table_privilege(c.oid, 'UPDATE') AS pode_atualizar
FROM pg_class c
LEFT JOIN pg_stat_all_tables stats ON stats.relid = c.oid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname IN (
       'dim_ies','dim_curso','dim_cine','dim_localizacao',
       'fato_censo_curso','fato_enade_curso',
       'vw_observatorio_censo_enade'
  )
ORDER BY c.relname;

-- Definições e validade reais dos índices nas tabelas do projeto.
SELECT c.relname AS tabela, idx.relname AS indice, i.indisunique AS unico,
       i.indisvalid AS valido, i.indisready AS pronto, pg_get_indexdef(idx.oid) AS definicao
FROM pg_index i
JOIN pg_class c ON c.oid = i.indrelid
JOIN pg_class idx ON idx.oid = i.indexrelid
WHERE c.oid IN (
    to_regclass('public.dim_ies'), to_regclass('public.dim_curso'),
    to_regclass('public.dim_cine'), to_regclass('public.dim_localizacao'),
    to_regclass('public.fato_censo_curso'), to_regclass('public.fato_enade_curso')
)
ORDER BY c.relname, idx.relname;

SELECT c.relname AS tabela, con.conname AS restricao, con.contype AS tipo,
       con.convalidated AS validada, pg_get_constraintdef(con.oid) AS definicao
FROM pg_constraint con
JOIN pg_class c ON c.oid = con.conrelid
WHERE c.oid IN (
    to_regclass('public.dim_ies'), to_regclass('public.dim_curso'),
    to_regclass('public.dim_cine'), to_regclass('public.dim_localizacao'),
    to_regclass('public.fato_censo_curso'), to_regclass('public.fato_enade_curso')
)
ORDER BY c.relname, con.conname;

SELECT pg_get_viewdef(c.oid, true) AS definicao_view
FROM pg_class c
WHERE c.oid = to_regclass('public.vw_observatorio_censo_enade')
  AND c.relkind IN ('v', 'm');


COMMIT;

-- Se o PG Studio nao permitir executar varios comandos simultaneamente,
-- execute os SELECTs isoladamente, sem BEGIN/COMMIT.
-- Somente rode sql/aiven_validacao_dados.sql depois de confirmar
-- que a view e as tabelas existem.
