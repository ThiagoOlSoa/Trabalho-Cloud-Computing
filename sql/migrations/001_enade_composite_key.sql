-- Execute com psql após conferir o esquema e as dependências reais.
\set ON_ERROR_STOP on
BEGIN;

LOCK TABLE public.fato_enade_curso IN ACCESS EXCLUSIVE MODE;

DO $$
DECLARE
    pk_name text;
    pk_columns text[];
BEGIN
    IF EXISTS (SELECT 1 FROM public.fato_enade_curso WHERE nu_ano IS NULL OR co_curso IS NULL) THEN
        RAISE EXCEPTION 'Migração 001: há chaves ENADE nulas.';
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.fato_enade_curso
        GROUP BY nu_ano, co_curso HAVING COUNT(*) > 1
    ) THEN
        RAISE EXCEPTION 'Migração 001: há chaves ENADE duplicadas. Consulte sql/auditoria_carga.sql.';
    END IF;

    SELECT c.conname, ARRAY(
        SELECT a.attname::text FROM unnest(c.conkey) WITH ORDINALITY AS k(attnum, ord)
        JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
        ORDER BY k.ord
    )
    INTO pk_name, pk_columns
    FROM pg_constraint c
    WHERE c.conrelid = 'public.fato_enade_curso'::regclass AND c.contype = 'p';

    IF pk_columns = ARRAY['nu_ano', 'co_curso'] THEN
        RETURN;
    END IF;
    IF pk_name IS NOT NULL THEN
        IF pk_columns <> ARRAY['co_curso'] THEN
            RAISE EXCEPTION 'Migração 001: chave primária inesperada (%). Revise o esquema.', pk_columns;
        END IF;
        EXECUTE format('ALTER TABLE public.fato_enade_curso DROP CONSTRAINT %I', pk_name);
    END IF;
    ALTER TABLE public.fato_enade_curso
        ADD CONSTRAINT fato_enade_curso_pkey PRIMARY KEY (nu_ano, co_curso);
END $$;

COMMIT;
