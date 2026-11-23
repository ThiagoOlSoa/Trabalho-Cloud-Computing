-- Consultas no mesmo universo padrão do dashboard: cursos da view.
-- Para reproduzir uma seleção, aplique o mesmo recorte à entrada de cada consulta.
-- 1) Composição de três populações do Censo 2024.
SELECT
    etapa,
    total,
    ROUND(100.0 * fem / NULLIF(total, 0), 1) AS pct_feminino,
    ROUND(100.0 * (preta + parda) / NULLIF(total - cornd, 0), 1)
        AS pct_negra_entre_racas_declaradas,
    ROUND(100.0 * cornd / NULLIF(total, 0), 1) AS pct_raca_nao_informada
FROM (
    SELECT 'Ingressantes' AS etapa, 1 AS ordem,
           SUM(qt_ing) AS total,
           SUM(qt_ing_fem_censo) AS fem,
           SUM(qt_ing_preta_censo) AS preta,
           SUM(qt_ing_parda_censo) AS parda,
           SUM(qt_ing_cornd_censo) AS cornd
    FROM public.vw_observatorio_censo_enade
    UNION ALL
    SELECT 'Matriculados', 2,
           SUM(qt_mat), SUM(qt_mat_fem_censo),
           SUM(qt_mat_preta_censo), SUM(qt_mat_parda_censo), SUM(qt_mat_cornd_censo)
    FROM public.vw_observatorio_censo_enade
    UNION ALL
    SELECT 'Concluintes', 3,
           SUM(qt_conc), SUM(qt_conc_fem_censo),
           SUM(qt_conc_preta_censo), SUM(qt_conc_parda_censo), SUM(qt_conc_cornd_censo)
    FROM public.vw_observatorio_censo_enade
) AS composicao
ORDER BY ordem;

-- 2) Matriz agregada de faixas de percentual feminino x percentual preta/parda.
-- O denominador de preta/parda exclui QT_MAT_CORND. Só cursos com >=30 matrículas.
-- Percentual desvinculado representa composição anual de situações de vínculo.
WITH perfil AS (
    SELECT
        co_curso,
        qt_mat,
        qt_conc,
        qt_sit_trancada,
        qt_sit_desvinculado,
        qt_mat + qt_sit_trancada + qt_sit_desvinculado
               + qt_sit_transferido + qt_sit_falecido AS total_situacoes,
        media_nt_ger,
        CASE WHEN possui_enade_2023 AND media_nt_ger BETWEEN 0 AND 100 AND qt_notas_validas > 0
             THEN qt_notas_validas ELSE 0 END AS peso_nota,
        100.0 * qt_mat_fem_censo / NULLIF(qt_mat, 0) AS pct_fem,
        100.0 * (qt_mat_preta_censo + qt_mat_parda_censo)
              / NULLIF(qt_mat - qt_mat_cornd_censo, 0) AS pct_negra
    FROM public.vw_observatorio_censo_enade
    WHERE qt_mat >= 30
), faixas AS (
    SELECT *,
        CASE WHEN pct_fem < 10 THEN '1) fem. < 10%'
             WHEN pct_fem <= 20 THEN '2) fem. 10-20%'
             ELSE '3) fem. > 20%' END AS faixa_feminino,
        CASE WHEN pct_negra < 25 THEN '1) preta/parda < 25%'
             WHEN pct_negra <= 50 THEN '2) preta/parda 25-50%'
             ELSE '3) preta/parda > 50%' END AS faixa_negra
    FROM perfil
    WHERE pct_negra IS NOT NULL AND pct_fem IS NOT NULL
)
SELECT
    faixa_feminino,
    faixa_negra,
    COUNT(*) AS cursos,
    SUM(qt_mat) AS matriculas,
    SUM(qt_conc) AS concluintes,
    ROUND(100.0 * SUM(qt_sit_desvinculado)
          / NULLIF(SUM(total_situacoes), 0), 1) AS pct_desvinculado_na_composicao,
    ROUND(100.0 * SUM(qt_sit_trancada)
          / NULLIF(SUM(total_situacoes), 0), 1) AS pct_trancada_na_composicao,
    COUNT(*) FILTER (WHERE peso_nota > 0) AS cursos_com_notas_enade,
    ROUND((SUM(media_nt_ger * peso_nota) FILTER (WHERE peso_nota > 0))
          / NULLIF(SUM(peso_nota), 0), 1) AS media_enade_ponderada
FROM faixas
GROUP BY faixa_feminino, faixa_negra
ORDER BY faixa_feminino, faixa_negra;

-- 3) A mesma matriz da consulta 2, separada por modalidade (presencial/EaD).
WITH perfil AS (
    SELECT
        co_curso,
        modalidade_ensino,
        qt_mat,
        qt_conc,
        qt_sit_trancada,
        qt_sit_desvinculado,
        qt_mat + qt_sit_trancada + qt_sit_desvinculado
               + qt_sit_transferido + qt_sit_falecido AS total_situacoes,
        media_nt_ger,
        CASE WHEN possui_enade_2023 AND media_nt_ger BETWEEN 0 AND 100 AND qt_notas_validas > 0
             THEN qt_notas_validas ELSE 0 END AS peso_nota,
        100.0 * qt_mat_fem_censo / NULLIF(qt_mat, 0) AS pct_fem,
        100.0 * (qt_mat_preta_censo + qt_mat_parda_censo)
              / NULLIF(qt_mat - qt_mat_cornd_censo, 0) AS pct_negra
    FROM public.vw_observatorio_censo_enade
    WHERE qt_mat >= 30
), faixas AS (
    SELECT *,
        modalidade_ensino AS modalidade,
        CASE WHEN pct_fem < 10 THEN '1) fem. < 10%'
             WHEN pct_fem <= 20 THEN '2) fem. 10-20%'
             ELSE '3) fem. > 20%' END AS faixa_feminino,
        CASE WHEN pct_negra < 25 THEN '1) preta/parda < 25%'
             WHEN pct_negra <= 50 THEN '2) preta/parda 25-50%'
             ELSE '3) preta/parda > 50%' END AS faixa_negra
    FROM perfil
    WHERE pct_negra IS NOT NULL AND pct_fem IS NOT NULL
)
SELECT
    modalidade,
    faixa_feminino,
    faixa_negra,
    COUNT(*) AS cursos,
    SUM(qt_mat) AS matriculas,
    SUM(qt_conc) AS concluintes,
    ROUND(100.0 * SUM(qt_sit_desvinculado)
          / NULLIF(SUM(total_situacoes), 0), 1) AS pct_desvinculado_na_composicao,
    ROUND(100.0 * SUM(qt_sit_trancada)
          / NULLIF(SUM(total_situacoes), 0), 1) AS pct_trancada_na_composicao,
    COUNT(*) FILTER (WHERE peso_nota > 0) AS cursos_com_notas_enade,
    ROUND((SUM(media_nt_ger * peso_nota) FILTER (WHERE peso_nota > 0))
          / NULLIF(SUM(peso_nota), 0), 1) AS media_enade_ponderada
FROM faixas
GROUP BY modalidade, faixa_feminino, faixa_negra
ORDER BY modalidade, faixa_feminino, faixa_negra;

-- 4) Transparência sobre raça/cor não informada, por grau e modalidade.
-- Censo e ENADE são denominadores distintos e devem ser lidos separadamente.
SELECT
    grau_academico,
    modalidade_ensino AS modalidade,
    COUNT(DISTINCT co_curso) FILTER (WHERE possui_enade_2023) AS cursos_com_enade,
    SUM(qt_mat) AS matriculas_censo,
    SUM(qt_mat_cornd_censo) AS matriculas_cor_raca_nao_informada,
    ROUND(100.0 * SUM(qt_mat_cornd_censo) / NULLIF(SUM(qt_mat), 0), 1)
        AS pct_cor_raca_nao_informada_censo,
    SUM(qt_participantes) AS participantes_enade,
    SUM(qt_raca_nao_declara + qt_raca_sem_resposta)
        AS participantes_enade_sem_declaracao_ou_resposta,
    ROUND(100.0 * SUM(qt_raca_nao_declara + qt_raca_sem_resposta)
          / NULLIF(SUM(qt_participantes), 0), 1)
        AS pct_sem_declaracao_ou_resposta_enade
FROM public.vw_observatorio_censo_enade
GROUP BY grau_academico, modalidade_ensino
ORDER BY grau_academico, modalidade_ensino;
