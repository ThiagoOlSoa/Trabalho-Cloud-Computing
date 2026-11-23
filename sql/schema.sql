-- Definição das tabelas dimensionais e fato do Observatório de Evasão e Retenção

CREATE TABLE IF NOT EXISTS dim_ies (
    co_ies INTEGER PRIMARY KEY,
    tp_rede INTEGER,
    tp_organizacao_academica INTEGER,
    tp_categoria_administrativa INTEGER,
    in_comunitaria INTEGER,
    in_confessional INTEGER
);

CREATE TABLE IF NOT EXISTS dim_curso (
    co_curso INTEGER PRIMARY KEY,
    co_ies INTEGER,
    no_curso TEXT,
    tp_grau_academico INTEGER,
    tp_modalidade_ensino INTEGER,
    tp_nivel_academico INTEGER,
    in_gratuito INTEGER
);

CREATE TABLE IF NOT EXISTS dim_cine (
    co_cine_rotulo VARCHAR(20) PRIMARY KEY,
    no_cine_rotulo TEXT,
    co_cine_area_detalhada VARCHAR(20),
    no_cine_area_detalhada TEXT,
    co_cine_area_especifica VARCHAR(20),
    no_cine_area_especifica TEXT,
    co_cine_area_geral VARCHAR(20),
    no_cine_area_geral TEXT
);

CREATE TABLE IF NOT EXISTS dim_localizacao (
    id_localizacao SERIAL PRIMARY KEY,
    co_municipio INTEGER,
    no_municipio TEXT,
    co_uf INTEGER,
    sg_uf VARCHAR(2),
    no_uf TEXT,
    co_regiao INTEGER,
    no_regiao TEXT,
    in_capital INTEGER
);

INSERT INTO dim_localizacao (no_municipio)
SELECT 'SEM MUNICÍPIO'
WHERE NOT EXISTS (
    SELECT 1 FROM dim_localizacao WHERE no_municipio = 'SEM MUNICÍPIO'
);

CREATE TABLE IF NOT EXISTS fato_censo_curso (
    id_fato SERIAL PRIMARY KEY,
    nu_ano_censo INTEGER NOT NULL,
    co_ies INTEGER NOT NULL REFERENCES dim_ies(co_ies),
    co_curso INTEGER NOT NULL REFERENCES dim_curso(co_curso),
    co_cine_rotulo VARCHAR(20) NOT NULL REFERENCES dim_cine(co_cine_rotulo),
    id_localizacao INTEGER NOT NULL REFERENCES dim_localizacao(id_localizacao),
    tp_dimensao INTEGER NOT NULL,
    qt_ing INTEGER NOT NULL CHECK (qt_ing >= 0),
    qt_ing_fem INTEGER NOT NULL CHECK (qt_ing_fem >= 0),
    qt_ing_masc INTEGER NOT NULL CHECK (qt_ing_masc >= 0),
    qt_ing_branca INTEGER NOT NULL CHECK (qt_ing_branca >= 0),
    qt_ing_preta INTEGER NOT NULL CHECK (qt_ing_preta >= 0),
    qt_ing_parda INTEGER NOT NULL CHECK (qt_ing_parda >= 0),
    qt_ing_amarela INTEGER NOT NULL CHECK (qt_ing_amarela >= 0),
    qt_ing_indigena INTEGER NOT NULL CHECK (qt_ing_indigena >= 0),
    qt_ing_cornd INTEGER NOT NULL CHECK (qt_ing_cornd >= 0),
    qt_mat INTEGER NOT NULL CHECK (qt_mat >= 0),
    qt_mat_fem INTEGER NOT NULL CHECK (qt_mat_fem >= 0),
    qt_mat_masc INTEGER NOT NULL CHECK (qt_mat_masc >= 0),
    qt_mat_branca INTEGER NOT NULL CHECK (qt_mat_branca >= 0),
    qt_mat_preta INTEGER NOT NULL CHECK (qt_mat_preta >= 0),
    qt_mat_parda INTEGER NOT NULL CHECK (qt_mat_parda >= 0),
    qt_mat_amarela INTEGER NOT NULL CHECK (qt_mat_amarela >= 0),
    qt_mat_indigena INTEGER NOT NULL CHECK (qt_mat_indigena >= 0),
    qt_mat_cornd INTEGER NOT NULL CHECK (qt_mat_cornd >= 0),
    qt_conc INTEGER NOT NULL CHECK (qt_conc >= 0),
    qt_conc_fem INTEGER NOT NULL CHECK (qt_conc_fem >= 0),
    qt_conc_masc INTEGER NOT NULL CHECK (qt_conc_masc >= 0),
    qt_conc_branca INTEGER NOT NULL CHECK (qt_conc_branca >= 0),
    qt_conc_preta INTEGER NOT NULL CHECK (qt_conc_preta >= 0),
    qt_conc_parda INTEGER NOT NULL CHECK (qt_conc_parda >= 0),
    qt_conc_amarela INTEGER NOT NULL CHECK (qt_conc_amarela >= 0),
    qt_conc_indigena INTEGER NOT NULL CHECK (qt_conc_indigena >= 0),
    qt_conc_cornd INTEGER NOT NULL CHECK (qt_conc_cornd >= 0),
    qt_sit_trancada INTEGER NOT NULL CHECK (qt_sit_trancada >= 0),
    qt_sit_desvinculado INTEGER NOT NULL CHECK (qt_sit_desvinculado >= 0),
    qt_sit_transferido INTEGER NOT NULL CHECK (qt_sit_transferido >= 0),
    qt_sit_falecido INTEGER NOT NULL CHECK (qt_sit_falecido >= 0),
    qt_ing_diurno INTEGER NOT NULL CHECK (qt_ing_diurno >= 0),
    qt_ing_noturno INTEGER NOT NULL CHECK (qt_ing_noturno >= 0),
    qt_mat_diurno INTEGER NOT NULL CHECK (qt_mat_diurno >= 0),
    qt_mat_noturno INTEGER NOT NULL CHECK (qt_mat_noturno >= 0),
    qt_conc_diurno INTEGER NOT NULL CHECK (qt_conc_diurno >= 0),
    qt_conc_noturno INTEGER NOT NULL CHECK (qt_conc_noturno >= 0),
    CONSTRAINT ck_censo_sexo_ing CHECK (qt_ing_fem + qt_ing_masc = qt_ing),
    CONSTRAINT ck_censo_raca_ing CHECK (qt_ing_branca + qt_ing_preta + qt_ing_parda + qt_ing_amarela + qt_ing_indigena + qt_ing_cornd = qt_ing),
    CONSTRAINT ck_censo_sexo_mat CHECK (qt_mat_fem + qt_mat_masc = qt_mat),
    CONSTRAINT ck_censo_raca_mat CHECK (qt_mat_branca + qt_mat_preta + qt_mat_parda + qt_mat_amarela + qt_mat_indigena + qt_mat_cornd = qt_mat),
    CONSTRAINT ck_censo_sexo_conc CHECK (qt_conc_fem + qt_conc_masc = qt_conc),
    CONSTRAINT ck_censo_raca_conc CHECK (qt_conc_branca + qt_conc_preta + qt_conc_parda + qt_conc_amarela + qt_conc_indigena + qt_conc_cornd = qt_conc)
);

CREATE TABLE IF NOT EXISTS fato_enade_curso (
    nu_ano INTEGER NOT NULL,
    co_curso INTEGER NOT NULL REFERENCES dim_curso(co_curso),
    co_ies_enade TEXT,
    co_grupo INTEGER,
    co_modalidade INTEGER CHECK (co_modalidade IN (0, 1)),
    co_uf_curso INTEGER,
    co_munic_curso INTEGER,
    co_regiao_curso INTEGER,
    qt_participantes INTEGER NOT NULL CHECK (qt_participantes >= 0),
    qt_notas_validas INTEGER NOT NULL CHECK (qt_notas_validas >= 0),
    media_nt_ger NUMERIC(10, 6) CHECK (media_nt_ger IS NULL OR media_nt_ger BETWEEN 0 AND 100),
    media_nt_fg NUMERIC(10, 6) CHECK (media_nt_fg IS NULL OR media_nt_fg BETWEEN 0 AND 100),
    media_nt_ce NUMERIC(10, 6) CHECK (media_nt_ce IS NULL OR media_nt_ce BETWEEN 0 AND 100),
    qt_sexo_f INTEGER NOT NULL CHECK (qt_sexo_f >= 0),
    qt_sexo_m INTEGER NOT NULL CHECK (qt_sexo_m >= 0),
    qt_raca_branca INTEGER NOT NULL CHECK (qt_raca_branca >= 0),
    qt_raca_preta INTEGER NOT NULL CHECK (qt_raca_preta >= 0),
    qt_raca_parda INTEGER NOT NULL CHECK (qt_raca_parda >= 0),
    qt_raca_amarela INTEGER NOT NULL CHECK (qt_raca_amarela >= 0),
    qt_raca_indigena INTEGER NOT NULL CHECK (qt_raca_indigena >= 0),
    qt_raca_nao_declara INTEGER NOT NULL CHECK (qt_raca_nao_declara >= 0),
    qt_raca_sem_resposta INTEGER NOT NULL CHECK (qt_raca_sem_resposta >= 0),
    PRIMARY KEY (nu_ano, co_curso),
    CONSTRAINT ck_enade_notas_validas CHECK (qt_notas_validas <= qt_participantes),
    CONSTRAINT ck_enade_sexo_total CHECK (qt_sexo_f + qt_sexo_m = qt_participantes),
    CONSTRAINT ck_enade_raca_total CHECK (
        qt_raca_branca + qt_raca_preta + qt_raca_parda + qt_raca_amarela
        + qt_raca_indigena + qt_raca_nao_declara + qt_raca_sem_resposta = qt_participantes
    )
);

-- Carga: rode src/load.py (Censo) antes de src/load_enade.py (ENADE), por causa da chave estrangeira.

-- Chaves naturais usadas pelo UPSERT do src/load.py (carga idempotente).
-- Municipio e unico na dimensao; a linha 'SEM MUNICIPIO' tem co_municipio NULL e nao conflita.
CREATE UNIQUE INDEX IF NOT EXISTS ux_dim_localizacao_municipio
    ON dim_localizacao (co_municipio);

-- Grao da fato: um registro por ano, curso, dimensao (1 presencial, 2 EaD, 3/4 outras) e localizacao.
CREATE UNIQUE INDEX IF NOT EXISTS ux_fato_censo_curso_grao
    ON fato_censo_curso (nu_ano_censo, co_curso, tp_dimensao, id_localizacao);
