-- Auditoria somente leitura. Campos diferentes contam como variantes.
BEGIN READ ONLY;

SELECT co_municipio, array_agg(id_localizacao ORDER BY id_localizacao) AS ids,
       count(DISTINCT (to_jsonb(l) - 'id_localizacao')) AS variantes
FROM public.dim_localizacao l
WHERE co_municipio IS NOT NULL
GROUP BY co_municipio
HAVING count(*) > 1;

SELECT array_agg(id_localizacao ORDER BY id_localizacao) AS localizacoes_sem_municipio
FROM public.dim_localizacao
WHERE co_municipio IS NULL AND no_municipio = 'SEM MUNICÍPIO';

-- Detecta colisões no grão atual e as que surgiriam se dois IDs do mesmo
-- município fossem consolidados. Mantém outras localizações sem município separadas.
SELECT f.nu_ano_censo, f.co_curso, f.tp_dimensao, l.co_municipio,
       array_agg(f.id_fato ORDER BY f.id_fato) AS ids_fato,
       array_agg(DISTINCT f.id_localizacao ORDER BY f.id_localizacao) AS ids_localizacao,
       count(DISTINCT (to_jsonb(f) - ARRAY['id_fato', 'id_localizacao'])) AS variantes
FROM public.fato_censo_curso f
LEFT JOIN public.dim_localizacao l USING (id_localizacao)
GROUP BY f.nu_ano_censo, f.co_curso, f.tp_dimensao, l.co_municipio,
         CASE WHEN l.co_municipio IS NULL AND l.no_municipio IS DISTINCT FROM 'SEM MUNICÍPIO'
              THEN f.id_localizacao END
HAVING count(*) > 1;

SELECT nu_ano, co_curso, count(*) AS linhas, count(DISTINCT to_jsonb(e)) AS variantes
FROM public.fato_enade_curso e
GROUP BY nu_ano, co_curso
HAVING count(*) > 1 OR nu_ano IS NULL OR co_curso IS NULL;

-- Visualiza colisões textuais após remover espaços e zeros à esquerda.
WITH chaves AS (
    SELECT nu_ano, co_curso::text AS original,
           ltrim(btrim(co_curso::text), '0') AS normalizado
    FROM public.fato_enade_curso
    WHERE btrim(co_curso::text) ~ '^[0-9]+$'
)
SELECT nu_ano, normalizado, array_agg(original ORDER BY original) AS chaves
FROM chaves
GROUP BY nu_ano, normalizado
HAVING count(*) > 1;

COMMIT;
