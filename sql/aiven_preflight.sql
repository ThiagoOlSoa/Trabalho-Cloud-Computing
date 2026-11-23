-- Etapa 6C: inventario somente leitura, seguro ate em banco vazio.
-- Pode ser executado no SQL Editor do PG Studio da Aiven.
-- Nao executa CREATE, INSERT, UPDATE, DELETE, ALTER ou DROP.
-- ATENCAO: nao compartilhe capturas que exponham nomes internos da conta.

BEGIN TRANSACTION READ ONLY;

SELECT current_database() AS banco,
       current_user AS usuario,
       current_setting('server_version') AS versao_pg,
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
            ELSE NULL END AS armazenamento
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname IN (
       'dim_ies','dim_curso','dim_cine','dim_localizacao',
       'fato_censo_curso','fato_enade_curso',
       'vw_observatorio_censo_enade'
  )
ORDER BY c.relname;

COMMIT;

-- Se o PG Studio nao permitir executar varios comandos simultaneamente,
-- execute os SELECTs isoladamente, sem BEGIN/COMMIT.
-- Somente rode sql/aiven_validacao_dados.sql depois de confirmar
-- que a view e as tabelas existem.
