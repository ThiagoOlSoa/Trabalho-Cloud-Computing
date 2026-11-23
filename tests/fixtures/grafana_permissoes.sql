-- Exemplo de concessão por coluna, com grafana_direto criado pelo administrador.
-- No teste, o papel é local e usa default_transaction_read_only = on.
GRANT USAGE ON SCHEMA public TO grafana_direto;
GRANT SELECT (
    nu_ano_censo, tp_dimensao, co_curso, co_ies, co_cine_rotulo, id_localizacao,
    qt_ing, qt_mat, qt_conc,
    qt_ing_fem, qt_ing_preta, qt_ing_parda, qt_ing_cornd,
    qt_mat_fem, qt_mat_preta, qt_mat_parda, qt_mat_cornd,
    qt_conc_fem, qt_conc_preta, qt_conc_parda, qt_conc_cornd,
    qt_sit_trancada, qt_sit_desvinculado, qt_sit_transferido, qt_sit_falecido
) ON public.fato_censo_curso TO grafana_direto;
GRANT SELECT (
    nu_ano, co_curso, co_modalidade, qt_participantes, qt_notas_validas,
    qt_raca_nao_declara, qt_raca_sem_resposta, media_nt_ger
) ON public.fato_enade_curso TO grafana_direto;
GRANT SELECT (co_curso, tp_grau_academico, tp_modalidade_ensino)
    ON public.dim_curso TO grafana_direto;
GRANT SELECT (co_ies, tp_rede) ON public.dim_ies TO grafana_direto;
GRANT SELECT (co_cine_rotulo, no_cine_rotulo) ON public.dim_cine TO grafana_direto;
GRANT SELECT (id_localizacao, sg_uf) ON public.dim_localizacao TO grafana_direto;
