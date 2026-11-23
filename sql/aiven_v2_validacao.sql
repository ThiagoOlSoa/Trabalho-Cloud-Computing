-- ETAPA 6E — TESTAR APÓS CRIAÇÃO APROVADA DA VIEW V2.
-- Somente leitura: não altera objetos ou dados.
SELECT
  COUNT(*) AS cursos,
  COUNT(*) FILTER (WHERE possui_enade_2023) AS com_enade,
  COUNT(*) FILTER (WHERE NOT possui_enade_2023) AS sem_enade,
  SUM(qt_mat) AS matriculas,
  SUM(qt_ing) AS ingressantes,
  SUM(qt_conc) AS concluintes,
  ROUND(100.0 * SUM(qt_mat_fem_censo) / NULLIF(SUM(qt_mat),0),1) AS pct_feminino,
  ROUND(100.0 * SUM(qt_mat_preta_censo + qt_mat_parda_censo)
       / NULLIF(SUM(qt_mat - qt_mat_cornd_censo),0),1) AS pct_preta_parda,
  ROUND(100.0 * SUM(qt_sit_desvinculado)
       / NULLIF(SUM(qt_mat + qt_sit_trancada + qt_sit_desvinculado
                    + qt_sit_transferido + qt_sit_falecido),0),1) AS pct_desvinculacao,
  ROUND(SUM(CASE WHEN possui_enade_2023 AND qt_notas_validas > 0
                     AND media_nt_ger BETWEEN 0 AND 100
                THEN media_nt_ger * qt_notas_validas ELSE 0 END)
         / NULLIF(SUM(CASE WHEN possui_enade_2023 AND qt_notas_validas > 0
                      AND media_nt_ger BETWEEN 0 AND 100
                      THEN qt_notas_validas ELSE 0 END),0),1) AS media_enade
FROM public.vw_observatorio_censo_enade_v2;
