SELECT
    CASE WHEN COUNT(qt_mat_cornd_censo) = COUNT(*) AND COUNT(qt_mat) = COUNT(*)
         THEN ROUND(100.0 * SUM(qt_mat_cornd_censo) /
                    NULLIF(GREATEST(SUM(qt_mat), 0), 0), 1) END AS censo,
    CASE WHEN COUNT(qt_raca_nao_declara + qt_raca_sem_resposta)
                  FILTER (WHERE possui_enade_2023) = COUNT(*) FILTER (WHERE possui_enade_2023)
               AND COUNT(qt_participantes) FILTER (WHERE possui_enade_2023)
                  = COUNT(*) FILTER (WHERE possui_enade_2023)
         THEN ROUND(100.0 * SUM(qt_raca_nao_declara + qt_raca_sem_resposta)
                                  FILTER (WHERE possui_enade_2023) /
                    NULLIF(GREATEST(SUM(qt_participantes)
                                  FILTER (WHERE possui_enade_2023), 0), 0), 1) END AS enade
FROM recorte
