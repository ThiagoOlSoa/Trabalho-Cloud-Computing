-- Migracao 003: integridade e tipos (NOT NULL, CHECKs, co_curso do ENADE como INTEGER, FK ENADE -> dim_curso).
-- FACA BACKUP ANTES. Rode DEPOIS da 002. Bancos novos ja recebem tudo pelo sql/schema.sql.
-- Se algum dado violar uma regra, a migracao inteira e desfeita (nada muda) e o erro mostra qual regra.
-- Ao final, a view e recriada automaticamente (\ir ../views.sql). Rode com psql, a partir da raiz do projeto:
--   psql -v ON_ERROR_STOP=1 -f sql/migrations/003_integridade_e_tipos.sql

\set ON_ERROR_STOP on
BEGIN;

LOCK TABLE public.dim_curso, public.fato_censo_curso, public.fato_enade_curso
    IN SHARE ROW EXCLUSIVE MODE;

DO $$
DECLARE
    course_type regtype;
BEGIN
    SELECT atttypid::regtype INTO STRICT course_type FROM pg_attribute
    WHERE attrelid = 'public.fato_enade_curso'::regclass AND attname = 'co_curso'
      AND NOT attisdropped;

    IF course_type NOT IN ('integer'::regtype, 'text'::regtype, 'varchar'::regtype) THEN
        RAISE EXCEPTION 'Migração 003: tipo de co_curso inesperado (%).', course_type;
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.fato_enade_curso
        WHERE nu_ano IS NULL OR co_curso IS NULL OR btrim(co_curso::text) !~ '^[0-9]+$'
    ) THEN
        RAISE EXCEPTION 'Migração 003: há chaves ENADE nulas ou inválidas.';
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.fato_enade_curso
        WHERE btrim(co_curso::text)::numeric NOT BETWEEN 1 AND 2147483647
    ) THEN
        RAISE EXCEPTION 'Migração 003: há códigos ENADE fora da faixa INTEGER positiva.';
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.fato_enade_curso
        GROUP BY nu_ano, btrim(co_curso::text)::integer HAVING count(*) > 1
    ) THEN
        RAISE EXCEPTION 'Migração 003: há colisões na chave ENADE após conversão.';
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.fato_enade_curso e
        LEFT JOIN public.dim_curso d ON d.co_curso = btrim(e.co_curso::text)::integer
        WHERE d.co_curso IS NULL
    ) THEN
        RAISE EXCEPTION 'Migração 003: há cursos ENADE sem correspondência no Censo.';
    END IF;

    IF course_type <> 'integer'::regtype THEN
        -- DROP RESTRICT e a transação preservam dependências em caso de falha.
        -- Uma view com metadados próprios precisa de migração específica.
        IF EXISTS (
            SELECT 1 FROM pg_class c
            WHERE c.oid = to_regclass('public.vw_observatorio_censo_enade')
              AND (c.relkind <> 'v' OR c.relowner <> current_user::regrole
                   OR c.relacl IS NOT NULL OR c.reloptions IS NOT NULL
                   OR obj_description(c.oid, 'pg_class') IS NOT NULL
                   OR EXISTS (
                       SELECT 1 FROM pg_attribute a WHERE a.attrelid = c.oid
                       AND (a.attacl IS NOT NULL OR col_description(c.oid, a.attnum) IS NOT NULL)
                   )
                   OR EXISTS (
                       SELECT 1 FROM pg_default_acl d WHERE d.defaclrole = current_user::regrole
                       AND d.defaclobjtype = 'r'
                       AND d.defaclnamespace IN (0, 'public'::regnamespace::oid)
                   ))
        ) THEN
            RAISE EXCEPTION 'Migração 003: a view ou o usuário de execução possui metadados próprios. Prepare uma migração que os preserve.';
        END IF;
        DROP VIEW IF EXISTS public.vw_observatorio_censo_enade RESTRICT;
        ALTER TABLE public.fato_enade_curso
            ALTER COLUMN co_curso TYPE INTEGER USING btrim(co_curso::text)::integer;
    END IF;
END $$;

-- 2) fato_censo_curso: NOT NULL nas chaves e nas medidas.
ALTER TABLE public.fato_censo_curso
    ALTER COLUMN nu_ano_censo SET NOT NULL,
    ALTER COLUMN co_ies SET NOT NULL,
    ALTER COLUMN co_curso SET NOT NULL,
    ALTER COLUMN co_cine_rotulo SET NOT NULL,
    ALTER COLUMN id_localizacao SET NOT NULL,
    ALTER COLUMN tp_dimensao SET NOT NULL,
    ALTER COLUMN qt_ing SET NOT NULL,
    ALTER COLUMN qt_ing_fem SET NOT NULL,
    ALTER COLUMN qt_ing_masc SET NOT NULL,
    ALTER COLUMN qt_ing_branca SET NOT NULL,
    ALTER COLUMN qt_ing_preta SET NOT NULL,
    ALTER COLUMN qt_ing_parda SET NOT NULL,
    ALTER COLUMN qt_ing_amarela SET NOT NULL,
    ALTER COLUMN qt_ing_indigena SET NOT NULL,
    ALTER COLUMN qt_ing_cornd SET NOT NULL,
    ALTER COLUMN qt_mat SET NOT NULL,
    ALTER COLUMN qt_mat_fem SET NOT NULL,
    ALTER COLUMN qt_mat_masc SET NOT NULL,
    ALTER COLUMN qt_mat_branca SET NOT NULL,
    ALTER COLUMN qt_mat_preta SET NOT NULL,
    ALTER COLUMN qt_mat_parda SET NOT NULL,
    ALTER COLUMN qt_mat_amarela SET NOT NULL,
    ALTER COLUMN qt_mat_indigena SET NOT NULL,
    ALTER COLUMN qt_mat_cornd SET NOT NULL,
    ALTER COLUMN qt_conc SET NOT NULL,
    ALTER COLUMN qt_conc_fem SET NOT NULL,
    ALTER COLUMN qt_conc_masc SET NOT NULL,
    ALTER COLUMN qt_conc_branca SET NOT NULL,
    ALTER COLUMN qt_conc_preta SET NOT NULL,
    ALTER COLUMN qt_conc_parda SET NOT NULL,
    ALTER COLUMN qt_conc_amarela SET NOT NULL,
    ALTER COLUMN qt_conc_indigena SET NOT NULL,
    ALTER COLUMN qt_conc_cornd SET NOT NULL,
    ALTER COLUMN qt_sit_trancada SET NOT NULL,
    ALTER COLUMN qt_sit_desvinculado SET NOT NULL,
    ALTER COLUMN qt_sit_transferido SET NOT NULL,
    ALTER COLUMN qt_sit_falecido SET NOT NULL,
    ALTER COLUMN qt_ing_diurno SET NOT NULL,
    ALTER COLUMN qt_ing_noturno SET NOT NULL,
    ALTER COLUMN qt_mat_diurno SET NOT NULL,
    ALTER COLUMN qt_mat_noturno SET NOT NULL,
    ALTER COLUMN qt_conc_diurno SET NOT NULL,
    ALTER COLUMN qt_conc_noturno SET NOT NULL;

-- 3) fato_censo_curso: valores nao negativos e totais consistentes.
ALTER TABLE public.fato_censo_curso
    DROP CONSTRAINT IF EXISTS ck_censo_nao_negativo,
    DROP CONSTRAINT IF EXISTS ck_censo_sexo_ing,
    DROP CONSTRAINT IF EXISTS ck_censo_raca_ing,
    DROP CONSTRAINT IF EXISTS ck_censo_sexo_mat,
    DROP CONSTRAINT IF EXISTS ck_censo_raca_mat,
    DROP CONSTRAINT IF EXISTS ck_censo_sexo_conc,
    DROP CONSTRAINT IF EXISTS ck_censo_raca_conc;

ALTER TABLE public.fato_censo_curso
    ADD CONSTRAINT ck_censo_nao_negativo CHECK (
        qt_ing >= 0
        AND qt_ing_fem >= 0
        AND qt_ing_masc >= 0
        AND qt_ing_branca >= 0
        AND qt_ing_preta >= 0
        AND qt_ing_parda >= 0
        AND qt_ing_amarela >= 0
        AND qt_ing_indigena >= 0
        AND qt_ing_cornd >= 0
        AND qt_mat >= 0
        AND qt_mat_fem >= 0
        AND qt_mat_masc >= 0
        AND qt_mat_branca >= 0
        AND qt_mat_preta >= 0
        AND qt_mat_parda >= 0
        AND qt_mat_amarela >= 0
        AND qt_mat_indigena >= 0
        AND qt_mat_cornd >= 0
        AND qt_conc >= 0
        AND qt_conc_fem >= 0
        AND qt_conc_masc >= 0
        AND qt_conc_branca >= 0
        AND qt_conc_preta >= 0
        AND qt_conc_parda >= 0
        AND qt_conc_amarela >= 0
        AND qt_conc_indigena >= 0
        AND qt_conc_cornd >= 0
        AND qt_sit_trancada >= 0
        AND qt_sit_desvinculado >= 0
        AND qt_sit_transferido >= 0
        AND qt_sit_falecido >= 0
        AND qt_ing_diurno >= 0
        AND qt_ing_noturno >= 0
        AND qt_mat_diurno >= 0
        AND qt_mat_noturno >= 0
        AND qt_conc_diurno >= 0
        AND qt_conc_noturno >= 0
    ),
    ADD CONSTRAINT ck_censo_sexo_ing CHECK (qt_ing_fem + qt_ing_masc = qt_ing),
    ADD CONSTRAINT ck_censo_raca_ing CHECK (qt_ing_branca + qt_ing_preta + qt_ing_parda + qt_ing_amarela + qt_ing_indigena + qt_ing_cornd = qt_ing),
    ADD CONSTRAINT ck_censo_sexo_mat CHECK (qt_mat_fem + qt_mat_masc = qt_mat),
    ADD CONSTRAINT ck_censo_raca_mat CHECK (qt_mat_branca + qt_mat_preta + qt_mat_parda + qt_mat_amarela + qt_mat_indigena + qt_mat_cornd = qt_mat),
    ADD CONSTRAINT ck_censo_sexo_conc CHECK (qt_conc_fem + qt_conc_masc = qt_conc),
    ADD CONSTRAINT ck_censo_raca_conc CHECK (qt_conc_branca + qt_conc_preta + qt_conc_parda + qt_conc_amarela + qt_conc_indigena + qt_conc_cornd = qt_conc);

-- 5) fato_enade_curso: NOT NULL nas medidas e regras de consistencia.
ALTER TABLE public.fato_enade_curso
    ALTER COLUMN qt_participantes SET NOT NULL,
    ALTER COLUMN qt_notas_validas SET NOT NULL,
    ALTER COLUMN qt_sexo_f SET NOT NULL,
    ALTER COLUMN qt_sexo_m SET NOT NULL,
    ALTER COLUMN qt_raca_branca SET NOT NULL,
    ALTER COLUMN qt_raca_preta SET NOT NULL,
    ALTER COLUMN qt_raca_parda SET NOT NULL,
    ALTER COLUMN qt_raca_amarela SET NOT NULL,
    ALTER COLUMN qt_raca_indigena SET NOT NULL,
    ALTER COLUMN qt_raca_nao_declara SET NOT NULL,
    ALTER COLUMN qt_raca_sem_resposta SET NOT NULL;

ALTER TABLE public.fato_enade_curso
    DROP CONSTRAINT IF EXISTS ck_fato_enade_sexo_total,
    DROP CONSTRAINT IF EXISTS ck_fato_enade_raca_total,
    DROP CONSTRAINT IF EXISTS ck_enade_nao_negativo,
    DROP CONSTRAINT IF EXISTS ck_enade_notas,
    DROP CONSTRAINT IF EXISTS ck_enade_notas_validas,
    DROP CONSTRAINT IF EXISTS ck_enade_sexo_total,
    DROP CONSTRAINT IF EXISTS ck_enade_raca_total;

ALTER TABLE public.fato_enade_curso
    ADD CONSTRAINT ck_enade_nao_negativo CHECK (
        qt_participantes >= 0 AND qt_notas_validas >= 0 AND qt_sexo_f >= 0 AND qt_sexo_m >= 0
        AND qt_raca_branca >= 0 AND qt_raca_preta >= 0 AND qt_raca_parda >= 0
        AND qt_raca_amarela >= 0 AND qt_raca_indigena >= 0
        AND qt_raca_nao_declara >= 0 AND qt_raca_sem_resposta >= 0
    ),
    ADD CONSTRAINT ck_enade_notas CHECK (
        (media_nt_ger IS NULL OR media_nt_ger BETWEEN 0 AND 100)
        AND (media_nt_fg IS NULL OR media_nt_fg BETWEEN 0 AND 100)
        AND (media_nt_ce IS NULL OR media_nt_ce BETWEEN 0 AND 100)
    ),
    ADD CONSTRAINT ck_enade_notas_validas CHECK (qt_notas_validas <= qt_participantes),
    ADD CONSTRAINT ck_enade_sexo_total CHECK (qt_sexo_f + qt_sexo_m = qt_participantes),
    ADD CONSTRAINT ck_enade_raca_total CHECK (
        qt_raca_branca + qt_raca_preta + qt_raca_parda + qt_raca_amarela
        + qt_raca_indigena + qt_raca_nao_declara + qt_raca_sem_resposta = qt_participantes
    );

-- 6) Preserva a FK equivalente do schema novo, mesmo com outro nome.
DO $$
DECLARE
    origem regclass := 'public.fato_enade_curso'::regclass;
    destino regclass := 'public.dim_curso'::regclass;
    fk_name text;
    fk_validated boolean;
BEGIN
    SELECT conname, convalidated INTO fk_name, fk_validated
    FROM pg_constraint
    WHERE contype = 'f' AND conrelid = origem AND confrelid = destino
      AND conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = origem
                          AND attname = 'co_curso' AND NOT attisdropped)]
      AND confkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = destino
                           AND attname = 'co_curso' AND NOT attisdropped)]
    ORDER BY convalidated DESC, conname LIMIT 1;

    IF fk_name IS NULL THEN
        ALTER TABLE public.fato_enade_curso
            ADD CONSTRAINT fk_enade_curso FOREIGN KEY (co_curso)
            REFERENCES public.dim_curso (co_curso);
    ELSIF NOT fk_validated THEN
        EXECUTE format('ALTER TABLE public.fato_enade_curso VALIDATE CONSTRAINT %I', fk_name);
    END IF;
END $$;

-- A definição aprovada é instalada na mesma transação, inclusive em caso de falha.
\ir ../views.sql

COMMIT;
