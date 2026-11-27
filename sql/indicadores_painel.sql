-- Uma linha por curso no recorte. COUNT(campo) invalida somas com lacunas.
SELECT
    COUNT(*) AS cursos,
    CASE WHEN COUNT(qt_mat) = COUNT(*) THEN SUM(qt_mat) END AS matriculas,
    CASE WHEN COUNT(qt_ing) = COUNT(*) THEN SUM(qt_ing) END AS ingressantes,
    CASE WHEN COUNT(qt_conc) = COUNT(*) THEN SUM(qt_conc) END AS concluintes,
    COUNT(*) FILTER (WHERE possui_enade_2023) AS cursos_enade,
    ROUND(100.0 * COUNT(*) FILTER (WHERE possui_enade_2023) /
          NULLIF(COUNT(*), 0), 1) AS cobertura,
    CASE WHEN COUNT(qt_mat_fem_censo) = COUNT(*) AND COUNT(qt_mat) = COUNT(*)
         THEN ROUND(100.0 * SUM(qt_mat_fem_censo) /
                    NULLIF(GREATEST(SUM(qt_mat), 0), 0), 1) END AS feminino,
    CASE WHEN COUNT(qt_mat_preta_censo + qt_mat_parda_censo) = COUNT(*)
               AND COUNT(qt_mat - qt_mat_cornd_censo) = COUNT(*)
         THEN ROUND(100.0 * SUM(qt_mat_preta_censo + qt_mat_parda_censo) /
                    NULLIF(GREATEST(SUM(qt_mat - qt_mat_cornd_censo), 0), 0), 1)
         END AS preta_parda,
    CASE WHEN COUNT(total_situacoes) = COUNT(*)
         THEN ROUND(100.0 * SUM(qt_sit_desvinculado) /
                    NULLIF(GREATEST(SUM(total_situacoes), 0), 0), 1) END AS desvinculacao,
    ROUND(SUM(media_nt_ger * peso_nota) FILTER (WHERE peso_nota > 0) /
          NULLIF(SUM(peso_nota), 0), 1) AS media_enade,
    COUNT(*) - COUNT(DISTINCT co_curso) AS chaves_invalidas
FROM cursos
