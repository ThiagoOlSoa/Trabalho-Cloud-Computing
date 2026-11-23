, perfil AS (
    SELECT *,
        100.0 * qt_mat_fem_censo / NULLIF(qt_mat, 0) AS pct_fem,
        100.0 * (qt_mat_preta_censo + qt_mat_parda_censo)
              / NULLIF(GREATEST(qt_mat - qt_mat_cornd_censo, 0), 0) AS pct_preta_parda
    FROM recorte
    WHERE qt_mat >= 30
), faixas AS (
    SELECT *,
           CASE WHEN pct_fem < 10 THEN '<10%' WHEN pct_fem <= 20 THEN '10–20%'
                ELSE '>20%' END AS faixa_fem,
           CASE WHEN pct_preta_parda < 25 THEN '<25%' WHEN pct_preta_parda <= 50 THEN '25–50%'
                ELSE '>50%' END AS faixa_preta_parda
    FROM perfil
    WHERE pct_fem IS NOT NULL AND pct_preta_parda IS NOT NULL
)
SELECT modalidade_ensino AS "Modalidade", faixa_fem AS "Faixa feminina",
    faixa_preta_parda AS "Faixa preta/parda", COUNT(*) AS "Cursos",
    SUM(qt_mat) AS "Matrículas",
    CASE WHEN COUNT(qt_conc) = COUNT(*) THEN SUM(qt_conc) END AS "Concluintes",
    CASE WHEN COUNT(total_situacoes) = COUNT(*)
         THEN ROUND(100.0 * SUM(qt_sit_desvinculado) /
                    NULLIF(GREATEST(SUM(total_situacoes), 0), 0), 1) END AS "Desvinculação (%)",
    ROUND(SUM(media_nt_ger * peso_nota) FILTER (WHERE peso_nota > 0) /
          NULLIF(SUM(peso_nota), 0), 1) AS "Média ENADE"
FROM faixas
GROUP BY modalidade_ensino, faixa_fem, faixa_preta_parda
ORDER BY modalidade_ensino,
         CASE faixa_fem WHEN '<10%' THEN 1 WHEN '10–20%' THEN 2 ELSE 3 END,
         CASE faixa_preta_parda WHEN '<25%' THEN 1 WHEN '25–50%' THEN 2 ELSE 3 END
