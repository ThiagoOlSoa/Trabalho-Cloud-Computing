-- Executar após revisar sql/auditoria_carga.sql. Nenhuma linha é removida.
\set ON_ERROR_STOP on
BEGIN;

LOCK TABLE public.dim_localizacao, public.fato_censo_curso IN SHARE ROW EXCLUSIVE MODE;

DO $$
BEGIN
    IF (SELECT count(*) FROM public.dim_localizacao
        WHERE co_municipio IS NULL AND no_municipio = 'SEM MUNICÍPIO') <> 1 THEN
        RAISE EXCEPTION 'Migração 002: esperada exatamente uma localização SEM MUNICÍPIO.';
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.dim_localizacao WHERE co_municipio IS NOT NULL
        GROUP BY co_municipio HAVING count(*) > 1
    ) OR EXISTS (
        SELECT 1 FROM public.fato_censo_curso
        GROUP BY nu_ano_censo, co_curso, tp_dimensao, id_localizacao HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'Migração 002: há duplicatas. Consulte sql/auditoria_carga.sql e revise os registros.';
    END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_localizacao_municipio
    ON public.dim_localizacao (co_municipio);
CREATE UNIQUE INDEX IF NOT EXISTS ux_fato_censo_curso_grao
    ON public.fato_censo_curso (nu_ano_censo, co_curso, tp_dimensao, id_localizacao);

-- Confirma que índices preexistentes permitem o UPSERT, sem executar gravações.
EXPLAIN INSERT INTO public.dim_localizacao (co_municipio) VALUES (1)
    ON CONFLICT (co_municipio) DO NOTHING;
EXPLAIN INSERT INTO public.fato_censo_curso (nu_ano_censo, co_curso, tp_dimensao, id_localizacao)
    VALUES (2024, 1, 1, 1)
    ON CONFLICT (nu_ano_censo, co_curso, tp_dimensao, id_localizacao) DO NOTHING;

COMMIT;
