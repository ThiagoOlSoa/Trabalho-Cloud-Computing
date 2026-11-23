-- ETAPA 6E — PRÉVIA SOMENTE LEITURA.
-- Executar PRIMEIRO no SQL Editor da Aiven, sem BEGIN/COMMIT.
-- Esta consulta executa a definição da view V2 como uma CTE, SEM criá-la.
-- Em caso de erro de coluna/tipo, NÃO rode o arquivo de criação.
WITH v2 AS (
WITH censo_curso AS (
    SELECT
        MIN(f.nu_ano_censo) AS nu_ano_censo,
        f.co_curso,
        MIN(f.co_ies) AS co_ies,
        MIN(f.co_cine_rotulo) AS co_cine_rotulo,
        MIN(f.id_localizacao) FILTER (WHERE f.tp_dimensao = 1) AS id_localizacao,
        SUM(f.qt_ing) AS qt_ing,
        SUM(f.qt_ing_fem) AS qt_ing_fem,
        SUM(f.qt_ing_masc) AS qt_ing_masc,
        SUM(f.qt_ing_branca) AS qt_ing_branca,
        SUM(f.qt_ing_preta) AS qt_ing_preta,
        SUM(f.qt_ing_parda) AS qt_ing_parda,
        SUM(f.qt_ing_amarela) AS qt_ing_amarela,
        SUM(f.qt_ing_indigena) AS qt_ing_indigena,
        SUM(f.qt_ing_cornd) AS qt_ing_cornd,
        SUM(f.qt_mat) AS qt_mat,
        SUM(f.qt_mat_fem) AS qt_mat_fem,
        SUM(f.qt_mat_masc) AS qt_mat_masc,
        SUM(f.qt_mat_branca) AS qt_mat_branca,
        SUM(f.qt_mat_preta) AS qt_mat_preta,
        SUM(f.qt_mat_parda) AS qt_mat_parda,
        SUM(f.qt_mat_amarela) AS qt_mat_amarela,
        SUM(f.qt_mat_indigena) AS qt_mat_indigena,
        SUM(f.qt_mat_cornd) AS qt_mat_cornd,
        SUM(f.qt_conc) AS qt_conc,
        SUM(f.qt_conc_fem) AS qt_conc_fem,
        SUM(f.qt_conc_masc) AS qt_conc_masc,
        SUM(f.qt_conc_branca) AS qt_conc_branca,
        SUM(f.qt_conc_preta) AS qt_conc_preta,
        SUM(f.qt_conc_parda) AS qt_conc_parda,
        SUM(f.qt_conc_amarela) AS qt_conc_amarela,
        SUM(f.qt_conc_indigena) AS qt_conc_indigena,
        SUM(f.qt_conc_cornd) AS qt_conc_cornd,
        SUM(f.qt_sit_trancada) AS qt_sit_trancada,
        SUM(f.qt_sit_desvinculado) AS qt_sit_desvinculado,
        SUM(f.qt_sit_transferido) AS qt_sit_transferido,
        SUM(f.qt_sit_falecido) AS qt_sit_falecido
    FROM public.fato_censo_curso AS f
    WHERE f.nu_ano_censo = 2024
      AND f.tp_dimensao IN (1, 2)
    GROUP BY f.co_curso
), enade_normalizado AS MATERIALIZED (
    SELECT e.*,
           CASE WHEN BTRIM(e.co_curso::text) ~ '^[0-9]+$'
                THEN COALESCE(NULLIF(LTRIM(BTRIM(e.co_curso::text), '0'), ''), '0')
           END AS co_curso_normalizado
    FROM public.fato_enade_curso AS e
    WHERE e.nu_ano = 2023
)
SELECT
    c.nu_ano_censo,
    e.nu_ano AS nu_ano_enade,
    (e.co_curso IS NOT NULL) AS possui_enade_2023,
    c.co_curso,
    dc.no_curso,
    dc.tp_grau_academico,
    CASE dc.tp_grau_academico
        WHEN 1 THEN 'Bacharelado'
        WHEN 2 THEN 'Licenciatura'
        WHEN 3 THEN 'Tecnológico'
        ELSE 'Outro / Não definido'
    END AS grau_academico,
    dc.tp_modalidade_ensino,
    CASE dc.tp_modalidade_ensino
        WHEN 1 THEN 'Presencial'
        WHEN 2 THEN 'EaD'
        ELSE 'Não informada'
    END AS modalidade_ensino,
    COALESCE(
        e.co_modalidade,
        CASE dc.tp_modalidade_ensino WHEN 1 THEN 1 WHEN 2 THEN 0 END
    ) AS co_modalidade,
    dc.in_gratuito,
    c.co_ies AS co_ies_censo,
    dies.tp_rede,
    CASE dies.tp_rede
        WHEN 1 THEN 'Pública'
        WHEN 2 THEN 'Privada'
        ELSE 'Não informada'
    END AS rede_ensino,
    e.co_ies_enade,
    CASE
        WHEN e.co_curso IS NULL THEN NULL
        ELSE c.co_ies::text = e.co_ies_enade::text
    END AS mesma_ies,
    c.co_cine_rotulo,
    cine.no_cine_rotulo,
    CASE
        WHEN dc.tp_modalidade_ensino = 2 OR e.co_modalidade = 0 THEN
            CASE e.co_uf_curso
                WHEN 11 THEN 'RO' WHEN 12 THEN 'AC' WHEN 13 THEN 'AM'
                WHEN 14 THEN 'RR' WHEN 15 THEN 'PA' WHEN 16 THEN 'AP'
                WHEN 17 THEN 'TO' WHEN 21 THEN 'MA' WHEN 22 THEN 'PI'
                WHEN 23 THEN 'CE' WHEN 24 THEN 'RN' WHEN 25 THEN 'PB'
                WHEN 26 THEN 'PE' WHEN 27 THEN 'AL' WHEN 28 THEN 'SE'
                WHEN 29 THEN 'BA' WHEN 31 THEN 'MG' WHEN 32 THEN 'ES'
                WHEN 33 THEN 'RJ' WHEN 35 THEN 'SP' WHEN 41 THEN 'PR'
                WHEN 42 THEN 'SC' WHEN 43 THEN 'RS' WHEN 50 THEN 'MS'
                WHEN 51 THEN 'MT' WHEN 52 THEN 'GO' WHEN 53 THEN 'DF'
                ELSE NULL
            END
        ELSE loc.sg_uf
    END AS sg_uf,
    e.co_uf_curso AS uf_curso_enade,
    c.qt_ing,
    c.qt_mat,
    c.qt_conc,
    c.qt_sit_trancada,
    c.qt_sit_desvinculado,
    c.qt_sit_transferido,
    c.qt_sit_falecido,
    COALESCE(e.qt_participantes, 0) AS qt_participantes,
    COALESCE(e.qt_notas_validas, 0) AS qt_notas_validas,
    e.media_nt_ger,
    e.media_nt_fg,
    e.media_nt_ce,
    COALESCE(e.qt_sexo_f, 0) AS qt_sexo_f,
    COALESCE(e.qt_sexo_m, 0) AS qt_sexo_m,
    COALESCE(e.qt_raca_branca, 0) AS qt_raca_branca,
    COALESCE(e.qt_raca_preta, 0) AS qt_raca_preta,
    COALESCE(e.qt_raca_parda, 0) AS qt_raca_parda,
    COALESCE(e.qt_raca_amarela, 0) AS qt_raca_amarela,
    COALESCE(e.qt_raca_indigena, 0) AS qt_raca_indigena,
    COALESCE(e.qt_raca_nao_declara, 0) AS qt_raca_nao_declara,
    COALESCE(e.qt_raca_sem_resposta, 0) AS qt_raca_sem_resposta,
    c.qt_ing_fem AS qt_ing_fem_censo,
    c.qt_ing_masc AS qt_ing_masc_censo,
    c.qt_ing_branca AS qt_ing_branca_censo,
    c.qt_ing_preta AS qt_ing_preta_censo,
    c.qt_ing_parda AS qt_ing_parda_censo,
    c.qt_ing_amarela AS qt_ing_amarela_censo,
    c.qt_ing_indigena AS qt_ing_indigena_censo,
    c.qt_ing_cornd AS qt_ing_cornd_censo,
    c.qt_mat_fem AS qt_mat_fem_censo,
    c.qt_mat_masc AS qt_mat_masc_censo,
    c.qt_mat_branca AS qt_mat_branca_censo,
    c.qt_mat_preta AS qt_mat_preta_censo,
    c.qt_mat_parda AS qt_mat_parda_censo,
    c.qt_mat_amarela AS qt_mat_amarela_censo,
    c.qt_mat_indigena AS qt_mat_indigena_censo,
    c.qt_mat_cornd AS qt_mat_cornd_censo,
    c.qt_conc_fem AS qt_conc_fem_censo,
    c.qt_conc_masc AS qt_conc_masc_censo,
    c.qt_conc_branca AS qt_conc_branca_censo,
    c.qt_conc_preta AS qt_conc_preta_censo,
    c.qt_conc_parda AS qt_conc_parda_censo,
    c.qt_conc_amarela AS qt_conc_amarela_censo,
    c.qt_conc_indigena AS qt_conc_indigena_censo,
    c.qt_conc_cornd AS qt_conc_cornd_censo
FROM censo_curso AS c
LEFT JOIN enade_normalizado AS e
       ON e.co_curso_normalizado = c.co_curso::text
LEFT JOIN public.dim_curso AS dc
       ON dc.co_curso = c.co_curso
LEFT JOIN public.dim_ies AS dies
       ON dies.co_ies = c.co_ies
LEFT JOIN public.dim_cine AS cine
       ON cine.co_cine_rotulo = c.co_cine_rotulo
LEFT JOIN public.dim_localizacao AS loc
       ON loc.id_localizacao = c.id_localizacao
)
SELECT
    COUNT(*) AS cursos,
    COUNT(DISTINCT co_curso) AS cursos_distintos,
    ROUND(100.0 * COUNT(*) FILTER (WHERE possui_enade_2023)
          / NULLIF(COUNT(*), 0), 1) AS cobertura_enade,
    COUNT(*) FILTER (WHERE possui_enade_2023) AS cursos_com_enade,
    COUNT(*) FILTER (WHERE NOT possui_enade_2023) AS cursos_sem_enade,
    SUM(qt_mat) AS matriculas,
    SUM(qt_ing) AS ingressantes,
    SUM(qt_conc) AS concluintes,
    ROUND(100.0 * SUM(qt_mat_fem_censo) / NULLIF(SUM(qt_mat), 0), 1) AS pct_feminino,
    ROUND(100.0 * SUM(qt_mat_preta_censo + qt_mat_parda_censo)
      / NULLIF(SUM(qt_mat - qt_mat_cornd_censo), 0), 1) AS pct_preta_parda,
    ROUND(100.0 * SUM(qt_sit_desvinculado)
      / NULLIF(SUM(qt_mat + qt_sit_trancada + qt_sit_desvinculado + qt_sit_transferido + qt_sit_falecido), 0), 1) AS pct_desvinculacao,
    ROUND(SUM(CASE WHEN possui_enade_2023 AND qt_notas_validas > 0
                      AND media_nt_ger BETWEEN 0 AND 100
                   THEN media_nt_ger * qt_notas_validas ELSE 0 END)
      / NULLIF(SUM(CASE WHEN possui_enade_2023 AND qt_notas_validas > 0
                         AND media_nt_ger BETWEEN 0 AND 100
                       THEN qt_notas_validas ELSE 0 END), 0), 1) AS media_enade
FROM v2;
