-- Somente para uma cópia local e descartável do esquema com os CSVs completos,
-- antes de instalar sql/views.sql nessa cópia.
BEGIN;
ALTER TABLE public.fato_enade_curso DROP CONSTRAINT fato_enade_curso_co_curso_fkey;
ALTER TABLE public.fato_enade_curso ALTER COLUMN co_curso TYPE varchar;
-- Exercita uma variante numérica legada sem presumir o tipo da nota na Aiven.
ALTER TABLE public.fato_enade_curso ALTER COLUMN media_nt_ger TYPE double precision;

-- Exercita espaços e zeros à esquerda sem alterar a quantidade de cursos.
UPDATE public.fato_enade_curso
SET co_curso = '  00' || co_curso || '  '
WHERE co_curso = (SELECT min(co_curso) FROM public.fato_enade_curso);

-- Reprodução mínima do comportamento conhecido da view antiga.
CREATE VIEW public.vw_observatorio_censo_enade AS
SELECT c.co_curso, e.nu_ano
FROM (SELECT DISTINCT co_curso FROM public.fato_censo_curso
      WHERE nu_ano_censo = 2024 AND tp_dimensao IN (1, 2)) c
JOIN public.fato_enade_curso e ON e.nu_ano = 2023
  AND LTRIM(BTRIM(e.co_curso), '0') = c.co_curso::text;
COMMIT;
