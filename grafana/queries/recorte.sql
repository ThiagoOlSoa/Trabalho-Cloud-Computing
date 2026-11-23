, recorte AS (
    SELECT *
    FROM cursos
    WHERE grau_academico = ANY(ARRAY[${grau:sqlstring}]::text[])
      AND modalidade_ensino = ANY(ARRAY[${modalidade:sqlstring}]::text[])
      AND rede_ensino = ANY(ARRAY[${rede:sqlstring}]::text[])
      AND uf_oferta = ANY(ARRAY[${uf:sqlstring}]::text[])
      AND area_cine = ANY(ARRAY[${cine:sqlstring}]::text[])
      AND (${enade:sqlstring} = 'Todos' OR possui_enade_2023)
)
