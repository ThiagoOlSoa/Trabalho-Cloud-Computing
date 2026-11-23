WITH censo_curso AS (
    SELECT f.co_curso,
           MIN(f.co_ies) AS co_ies,
           MIN(f.co_cine_rotulo) AS co_cine_rotulo,
           MIN(f.id_localizacao) FILTER (WHERE f.tp_dimensao = 1) AS id_localizacao,
           SUM(f.qt_ing) AS qt_ing,
           SUM(f.qt_mat) AS qt_mat,
           SUM(f.qt_conc) AS qt_conc,
           SUM(f.qt_ing_fem) AS qt_ing_fem_censo,
           SUM(f.qt_ing_preta) AS qt_ing_preta_censo,
           SUM(f.qt_ing_parda) AS qt_ing_parda_censo,
           SUM(f.qt_ing_cornd) AS qt_ing_cornd_censo,
           SUM(f.qt_mat_fem) AS qt_mat_fem_censo,
           SUM(f.qt_mat_preta) AS qt_mat_preta_censo,
           SUM(f.qt_mat_parda) AS qt_mat_parda_censo,
           SUM(f.qt_mat_cornd) AS qt_mat_cornd_censo,
           SUM(f.qt_conc_fem) AS qt_conc_fem_censo,
           SUM(f.qt_conc_preta) AS qt_conc_preta_censo,
           SUM(f.qt_conc_parda) AS qt_conc_parda_censo,
           SUM(f.qt_conc_cornd) AS qt_conc_cornd_censo,
           SUM(f.qt_sit_trancada) AS qt_sit_trancada,
           SUM(f.qt_sit_desvinculado) AS qt_sit_desvinculado,
           SUM(f.qt_sit_transferido) AS qt_sit_transferido,
           SUM(f.qt_sit_falecido) AS qt_sit_falecido
    FROM public.fato_censo_curso AS f
    WHERE f.nu_ano_censo = 2024 AND f.tp_dimensao IN (1, 2)
    GROUP BY f.co_curso
), enade_normalizado AS MATERIALIZED (
    -- O texto evita overflow e é calculado uma vez por registro da edição.
    SELECT CASE WHEN BTRIM(e.co_curso::text) ~ '^[0-9]+$'
                THEN COALESCE(NULLIF(LTRIM(BTRIM(e.co_curso::text), '0'), ''), '0')
           END AS chave_curso,
           e.co_modalidade, e.qt_participantes, e.qt_notas_validas,
           e.qt_raca_nao_declara, e.qt_raca_sem_resposta, e.media_nt_ger::numeric AS media_nt_ger
    FROM public.fato_enade_curso AS e
    WHERE e.nu_ano = 2023
), cursos AS (
    SELECT c.*,
           CASE dc.tp_grau_academico
               WHEN 1 THEN 'Bacharelado' WHEN 2 THEN 'Licenciatura'
               WHEN 3 THEN 'Tecnológico' ELSE 'Outro / Não definido'
           END AS grau_academico,
           CASE dc.tp_modalidade_ensino
               WHEN 1 THEN 'Presencial' WHEN 2 THEN 'EaD' ELSE 'Não informada'
           END AS modalidade_ensino,
           CASE ies.tp_rede
               WHEN 1 THEN 'Pública' WHEN 2 THEN 'Privada' ELSE 'Não informada'
           END AS rede_ensino,
           COALESCE(NULLIF(cine.no_cine_rotulo, ''), 'Não informado') AS area_cine,
           CASE WHEN dc.tp_modalidade_ensino = 2 THEN 'EaD · UF não atribuída'
                WHEN dc.tp_modalidade_ensino = 1 AND e.co_modalidade IS DISTINCT FROM 0
                THEN COALESCE(NULLIF(loc.sg_uf, ''), 'UF indisponível')
                ELSE 'UF indisponível' END AS uf_oferta,
           e.chave_curso IS NOT NULL AS possui_enade_2023,
           COALESCE(e.qt_participantes, 0) AS qt_participantes,
           COALESCE(e.qt_raca_nao_declara, 0) AS qt_raca_nao_declara,
           COALESCE(e.qt_raca_sem_resposta, 0) AS qt_raca_sem_resposta,
           e.media_nt_ger,
           CASE WHEN e.media_nt_ger BETWEEN 0 AND 100 AND e.qt_notas_validas > 0
                THEN e.qt_notas_validas ELSE 0 END AS peso_nota,
           c.qt_mat + c.qt_sit_trancada + c.qt_sit_desvinculado
               + c.qt_sit_transferido + c.qt_sit_falecido AS total_situacoes
    FROM censo_curso AS c
    LEFT JOIN enade_normalizado AS e ON e.chave_curso = c.co_curso::text
    LEFT JOIN public.dim_curso AS dc ON dc.co_curso = c.co_curso
    LEFT JOIN public.dim_ies AS ies ON ies.co_ies = c.co_ies
    LEFT JOIN public.dim_cine AS cine ON cine.co_cine_rotulo = c.co_cine_rotulo
    LEFT JOIN public.dim_localizacao AS loc ON loc.id_localizacao = c.id_localizacao
)
