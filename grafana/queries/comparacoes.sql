SELECT categoria AS "Categoria",
    CASE WHEN COUNT(qt_mat_fem_censo) = COUNT(*) AND COUNT(qt_mat) = COUNT(*)
         THEN ROUND(100.0 * SUM(qt_mat_fem_censo) /
                    NULLIF(GREATEST(SUM(qt_mat), 0), 0), 1) END AS "Feminina (%)",
    CASE WHEN COUNT(qt_mat_preta_censo + qt_mat_parda_censo) = COUNT(*)
               AND COUNT(qt_mat - qt_mat_cornd_censo) = COUNT(*)
         THEN ROUND(100.0 * SUM(qt_mat_preta_censo + qt_mat_parda_censo) /
                    NULLIF(GREATEST(SUM(qt_mat - qt_mat_cornd_censo), 0), 0), 1)
         END AS "Preta/parda (%)"
FROM recorte
CROSS JOIN LATERAL (VALUES ({{grupo}})) AS rotulo(categoria)
GROUP BY categoria
ORDER BY categoria
