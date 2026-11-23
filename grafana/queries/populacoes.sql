SELECT p.populacao AS "População",
    CASE WHEN COUNT(p.total) = COUNT(*) THEN SUM(p.total) END AS "Total",
    CASE WHEN COUNT(p.fem) = COUNT(*) AND COUNT(p.total) = COUNT(*)
         THEN ROUND(100.0 * SUM(p.fem) /
                    NULLIF(GREATEST(SUM(p.total), 0), 0), 1) END AS "Feminina (%)",
    CASE WHEN COUNT(p.preta_parda) = COUNT(*) AND COUNT(p.total - p.cornd) = COUNT(*)
         THEN ROUND(100.0 * SUM(p.preta_parda) /
                    NULLIF(GREATEST(SUM(p.total - p.cornd), 0), 0), 1)
         END AS "Preta/parda (%)"
FROM recorte
CROSS JOIN LATERAL (VALUES
    (1, 'Ingressantes', qt_ing, qt_ing_fem_censo,
        qt_ing_preta_censo + qt_ing_parda_censo, qt_ing_cornd_censo),
    (2, 'Matriculados', qt_mat, qt_mat_fem_censo,
        qt_mat_preta_censo + qt_mat_parda_censo, qt_mat_cornd_censo),
    (3, 'Concluintes', qt_conc, qt_conc_fem_censo,
        qt_conc_preta_censo + qt_conc_parda_censo, qt_conc_cornd_censo)
) AS p(ordem, populacao, total, fem, preta_parda, cornd)
GROUP BY p.ordem, p.populacao
ORDER BY p.ordem
