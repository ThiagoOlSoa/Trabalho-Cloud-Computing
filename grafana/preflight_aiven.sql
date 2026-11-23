-- Execute como administrador para inventariar o esquema e depois como o papel Grafana.
-- A consulta é somente leitura. Deve retornar tipo_ok = true e pode_ler = true em todas as linhas.
WITH grupos(tabela, tipos, colunas) AS (
    VALUES
        ('fato_censo_curso', ARRAY['int2', 'int4', 'int8'],
         ARRAY['nu_ano_censo', 'tp_dimensao', 'co_curso', 'co_ies', 'id_localizacao',
               'qt_ing', 'qt_mat', 'qt_conc',
               'qt_ing_fem', 'qt_ing_preta', 'qt_ing_parda', 'qt_ing_cornd',
               'qt_mat_fem', 'qt_mat_preta', 'qt_mat_parda', 'qt_mat_cornd',
               'qt_conc_fem', 'qt_conc_preta', 'qt_conc_parda', 'qt_conc_cornd',
               'qt_sit_trancada', 'qt_sit_desvinculado', 'qt_sit_transferido', 'qt_sit_falecido']),
        ('fato_censo_curso', ARRAY['varchar', 'text'], ARRAY['co_cine_rotulo']),
        ('fato_enade_curso', ARRAY['varchar', 'text', 'int2', 'int4', 'int8'], ARRAY['co_curso']),
        ('fato_enade_curso', ARRAY['int2', 'int4', 'int8'],
         ARRAY['nu_ano', 'co_modalidade', 'qt_participantes', 'qt_notas_validas',
               'qt_raca_nao_declara', 'qt_raca_sem_resposta']),
        ('fato_enade_curso', ARRAY['numeric', 'float4', 'float8', 'int2', 'int4', 'int8'],
         ARRAY['media_nt_ger']),
        ('dim_curso', ARRAY['int2', 'int4', 'int8'],
         ARRAY['co_curso', 'tp_grau_academico', 'tp_modalidade_ensino']),
        ('dim_ies', ARRAY['int2', 'int4', 'int8'], ARRAY['co_ies', 'tp_rede']),
        ('dim_cine', ARRAY['varchar', 'text'], ARRAY['co_cine_rotulo', 'no_cine_rotulo']),
        ('dim_localizacao', ARRAY['int2', 'int4', 'int8'], ARRAY['id_localizacao']),
        ('dim_localizacao', ARRAY['varchar', 'text', 'bpchar'], ARRAY['sg_uf'])
), esperadas AS (
    SELECT tabela, tipos, unnest(colunas) AS coluna FROM grupos
)
SELECT e.tabela, e.coluna, format_type(a.atttypid, a.atttypmod) AS tipo,
       COALESCE(t.typname = ANY(e.tipos), FALSE) AS tipo_ok,
       COALESCE(has_column_privilege(c.oid, a.attnum, 'SELECT'), FALSE) AS pode_ler
FROM esperadas AS e
LEFT JOIN pg_namespace AS n ON n.nspname = 'public'
LEFT JOIN pg_class AS c ON c.relnamespace = n.oid AND c.relname = e.tabela
LEFT JOIN pg_attribute AS a
       ON a.attrelid = c.oid AND a.attname = e.coluna AND a.attnum > 0 AND NOT a.attisdropped
LEFT JOIN pg_type AS t ON t.oid = a.atttypid
ORDER BY e.tabela, e.coluna;

-- Esperado: 1.665 registros, 1.665 chaves normalizadas válidas e 1.665 distintas.
WITH chaves AS (
    SELECT CASE WHEN BTRIM(co_curso::text) ~ '^[0-9]+$'
                THEN COALESCE(NULLIF(LTRIM(BTRIM(co_curso::text), '0'), ''), '0')
           END AS chave
    FROM public.fato_enade_curso
    WHERE nu_ano = 2023
)
SELECT COUNT(*) AS registros_2023, COUNT(chave) AS chaves_validas,
       COUNT(DISTINCT chave) AS chaves_distintas
FROM chaves;
