-- Etapa 6C: executar SOMENTE depois da confirmacao de que
-- public.vw_observatorio_censo_enade existe e esta acessivel.
-- Esta consulta e somente leitura; nenhum dado e modificado.
-- Os resultados sao referencias para o recorte Censo 2024 + ENADE 2023.

BEGIN TRANSACTION READ ONLY;

SELECT
    COUNT(*) AS cursos,
    COALESCE(SUM(qt_mat), 0) AS matriculas,
    COALESCE(SUM(qt_ing), 0) AS ingressantes,
    COALESCE(SUM(qt_conc), 0) AS concluintes,
    COUNT(*) FILTER (WHERE possui_enade_2023) AS cursos_com_enade,
    ROUND(100.0 * SUM(qt_mat_fem_censo) / NULLIF(SUM(qt_mat),0), 1) AS percentual_feminino,
    ROUND(100.0 * SUM(qt_mat_preta_censo + qt_mat_parda_censo)
                  / NULLIF(SUM(qt_mat - qt_mat_cornd_censo),0), 1) AS percentual_preta_parda,
    ROUND(100.0 * SUM(qt_sit_desvinculado)
                  / NULLIF(SUM(qt_mat + qt_sit_trancada + qt_sit_desvinculado
                                   + qt_sit_transferido + qt_sit_falecido),0), 1) AS percentual_desvinculacao,
    ROUND(
      SUM(CASE WHEN possui_enade_2023 AND qt_notas_validas > 0
                    AND media_nt_ger BETWEEN 0 AND 100
               THEN media_nt_ger * qt_notas_validas ELSE 0 END)
      / NULLIF(SUM(CASE WHEN possui_enade_2023 AND qt_notas_validas > 0
                             AND media_nt_ger BETWEEN 0 AND 100
                        THEN qt_notas_validas ELSE 0 END), 0), 1
    ) AS media_enade_ponderada
FROM public.vw_observatorio_censo_enade;

SELECT COUNT(*) AS linhas_fato_censo FROM public.fato_censo_curso;
SELECT COUNT(*) AS linhas_fato_enade FROM public.fato_enade_curso;
SELECT COUNT(*) AS cursos_distintos_geral FROM public.dim_curso;

COMMIT;

-- Referencias locais: 7.078 cursos na view, 1.269.093 matriculas,
-- 673.375 ingressantes, 153.760 concluintes, 1.665 cursos ENADE,
-- 20,2% feminino, 41,2% preta/parda, 21,7% desvinculacao,
-- media ENADE 41,8; fato Censo 110.022 linhas, 7.085 cursos.
-- Se divergente, NAO sobrescreva nem aplique migracoes sem diagnostico.
