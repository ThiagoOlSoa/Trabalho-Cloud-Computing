WITH cursos AS (
    SELECT v.*,
           COALESCE(NULLIF(v.no_cine_rotulo, ''), 'Não informado') AS area_cine,
           CASE WHEN v.tp_modalidade_ensino = 2 THEN 'EaD · UF não atribuída'
                WHEN v.tp_modalidade_ensino = 1 AND v.co_modalidade IS DISTINCT FROM 0
                THEN COALESCE(NULLIF(v.sg_uf, ''), 'UF indisponível')
                ELSE 'UF indisponível' END AS uf_oferta,
           v.qt_mat + v.qt_sit_trancada + v.qt_sit_desvinculado
               + v.qt_sit_transferido + v.qt_sit_falecido AS total_situacoes,
           CASE WHEN v.possui_enade_2023 AND v.media_nt_ger BETWEEN 0 AND 100
                     AND v.qt_notas_validas > 0
                THEN v.qt_notas_validas ELSE 0 END AS peso_nota
    FROM public.vw_observatorio_censo_enade AS v
)
