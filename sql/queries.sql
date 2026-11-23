-- 1) Validação de granularidade e cobertura Censo–ENADE.
-- A view mantém todos os cursos do Censo; as colunas filtradas identificam
-- a subamostra ENADE, que deve ter 1.665 cursos e 279.158 matrículas Censo.
SELECT
    COUNT(*) AS linhas_na_view,
    COUNT(DISTINCT co_curso) AS cursos_distintos_na_view,
    COUNT(*) FILTER (WHERE possui_enade_2023) AS linhas_com_enade_2023,
    COUNT(DISTINCT co_curso) FILTER (WHERE possui_enade_2023)
        AS cursos_com_enade_2023,
    SUM(qt_mat) AS matriculas_todos_os_cursos,
    SUM(qt_mat) FILTER (WHERE possui_enade_2023)
        AS matriculas_nos_cursos_com_enade
FROM public.vw_observatorio_censo_enade;

-- Esperado com os CSVs incluídos: 7.078 linhas/cursos na view;
-- 1.665 cursos com ENADE 2023; 279.158 matrículas nesse subconjunto.

-- 2) Cobertura por grau acadêmico. Cursos sem ENADE permanecem na view.
SELECT
    grau_academico,
    COUNT(*) AS cursos_censo_2024,
    COUNT(*) FILTER (WHERE possui_enade_2023) AS cursos_com_enade_2023,
    SUM(qt_mat) AS matriculas_2024,
    SUM(qt_conc) AS concluintes_2024
FROM public.vw_observatorio_censo_enade
GROUP BY grau_academico
ORDER BY matriculas_2024 DESC;

-- 3) Cobertura ENADE por modalidade: presencial=1, EaD=0.
-- Esperado com os CSVs incluídos: 1.553 presenciais e 112 EaD.
SELECT
    co_modalidade,
    CASE co_modalidade WHEN 1 THEN 'Presencial' WHEN 0 THEN 'EaD'
         ELSE 'Não informada' END AS modalidade,
    COUNT(*) AS cursos
FROM public.vw_observatorio_censo_enade
WHERE possui_enade_2023
GROUP BY co_modalidade
ORDER BY co_modalidade;
