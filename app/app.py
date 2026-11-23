import logging
import os
from contextlib import ExitStack, closing
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Observatório de Evasão e Retenção — Área 1",
    layout="wide",
)

st.markdown("""
<style>
.observatorio-hero {
  padding: clamp(1.25rem, 4vw, 2.6rem);
  border-radius: 1rem;
  background: linear-gradient(115deg, #17324D 0%, #195C72 65%, #176E7A 100%);
  color: #fff;
}
.observatorio-hero h1 {
  color: inherit;
  font-size: clamp(1.9rem, 4.4vw, 3.1rem);
  line-height: 1.07;
  letter-spacing: -.035em;
  padding: 0;
  margin: .45rem 0 .65rem;
}
.observatorio-hero p { color: #E5F2F4; margin: .45rem 0 0; }
.observatorio-hero .observatorio-contexto {
  color: #CFEBEF;
  font-size: .8rem;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
}
.st-key-cartoes_observatorio :where([class*="st-key-kpi_"]) {
  background: #fff;
  color: #17324D;
  border: 1px solid #D9E5ED;
  border-radius: .8rem;
  padding: .85rem 1rem;
  border-top: .22rem solid #167D8D;
  height: 100%;
}
.st-key-cartoes_observatorio :where([class*="st-key-kpi_zero_"]) {
  border-top-color: #647C8E;
}
.st-key-cartoes_observatorio :where([class*="st-key-kpi_ausente_"]) {
  border-top-color: #C08B28;
  background: #FFFBF3;
}
</style>
""", unsafe_allow_html=True)

GRAU_MAP = {
    1: "Bacharelado",
    2: "Licenciatura",
    3: "Tecnológico",
}

MODALIDADE_CENSO_MAP = {
    1: "Presencial",
    2: "EaD",
}

REDE_MAP = {
    1: "Pública",
    2: "Privada",
}


CONFIGURACAO = (
    "APP_DATA_MODE", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
    "DB_SSLMODE", "DB_SSLROOTCERT", "DB_SSL_CA_PEM",
)
CAMPOS_POSTGRES = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")


def ler_configuracao():
    try:
        # Força a leitura do TOML antes de consultar o ambiente. A seção
        # [observatorio] permanece no objeto de Secrets do Streamlit.
        segredos = st.secrets.get("observatorio", {})
    except FileNotFoundError:
        segredos = {}
    return {nome: os.environ.get(nome, segredos.get(nome, "")) for nome in CONFIGURACAO}


def carregar_via_aiven(config) -> pd.DataFrame:
    import psycopg2

    host = str(config["DB_HOST"]).strip()
    socket_local = host.startswith("/")
    local = socket_local or host in ("127.0.0.1", "::1", "localhost")
    faltantes = [
        nome for nome in CAMPOS_POSTGRES if not config[nome]
        and not (nome == "DB_PASSWORD" and socket_local)
    ]
    if faltantes:
        raise ValueError("Configuração PostgreSQL incompleta")

    porta = int(config["DB_PORT"])
    if not 1 <= porta <= 65535:
        raise ValueError("Porta PostgreSQL inválida")
    sslmode = config["DB_SSLMODE"] or "require"
    if sslmode not in ("require", "verify-ca", "verify-full") and not (local and sslmode == "disable"):
        raise ValueError("Modo TLS inválido")
    ca_path, ca_pem = config["DB_SSLROOTCERT"], config["DB_SSL_CA_PEM"]
    if ca_path and ca_pem:
        raise ValueError("Informe uma única origem para a CA")
    if sslmode.startswith("verify-") and not (ca_path or ca_pem):
        raise ValueError("CA necessária para verificar o servidor")

    with ExitStack() as stack:
        ssl_options = {}
        if ca_pem:
            directory = stack.enter_context(TemporaryDirectory(prefix="observatorio-ca-"))
            ca_file = Path(directory) / "ca.pem"
            ca_file.write_text(ca_pem, encoding="utf-8")
            ca_path = str(ca_file)
        if ca_path:
            ssl_options["sslrootcert"] = ca_path

        conn = stack.enter_context(closing(psycopg2.connect(
            host=host, port=porta, dbname=config["DB_NAME"], user=config["DB_USER"],
            password=config["DB_PASSWORD"], sslmode=sslmode, connect_timeout=5,
            options="-c default_transaction_read_only=on -c statement_timeout=15000",
            **ssl_options,
        )))
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM public.vw_observatorio_censo_enade;")
            return pd.DataFrame.from_records(
                cursor.fetchall(), columns=[column.name.lower() for column in cursor.description],
                coerce_float=True,
            )


carregar_postgres_cache = st.cache_data(ttl=120, max_entries=2, show_spinner=False)(carregar_via_aiven)


@st.cache_data(ttl=120, max_entries=2, show_spinner="Carregando arquivos locais...")
def carregar_via_csv_local(raiz: Path | None = None) -> pd.DataFrame | None:
    raiz = raiz or Path(__file__).resolve().parents[1]
    pasta = raiz / "data" / "processed"

    def localizar_csv(nome):
        # Prefere CSV convencional em ambiente local e aceita gzip no deploy.
        caminho = pasta / f"{nome}.csv"
        if caminho.is_file():
            return caminho
        comprimido = pasta / f"{nome}.csv.gz"
        return comprimido if comprimido.is_file() else None

    censo_path = localizar_csv("censo_2024_area1")
    enade_path = localizar_csv("enade_2023_area1")
    if censo_path is None or enade_path is None:
        return None

    censo = pd.read_csv(censo_path, sep=";", encoding="cp1252", low_memory=False)
    censo["CO_CINE_ROTULO"] = (
        censo["CO_CINE_ROTULO"].astype(str).str.strip().str.strip('"')
    )

    # Mesma regra da views.sql: TP_DIMENSAO IN (1, 2) agrupado por CO_CURSO
    censo_f = censo[
        (censo["NU_ANO_CENSO"] == 2024) & (censo["TP_DIMENSAO"].isin([1, 2]))
    ].copy()

    cols_soma = [
        "QT_ING", "QT_ING_FEM", "QT_ING_MASC",
        "QT_ING_BRANCA", "QT_ING_PRETA", "QT_ING_PARDA",
        "QT_ING_AMARELA", "QT_ING_INDIGENA", "QT_ING_CORND",
        "QT_MAT", "QT_MAT_FEM", "QT_MAT_MASC",
        "QT_MAT_BRANCA", "QT_MAT_PRETA", "QT_MAT_PARDA",
        "QT_MAT_AMARELA", "QT_MAT_INDIGENA", "QT_MAT_CORND",
        "QT_CONC", "QT_CONC_FEM", "QT_CONC_MASC",
        "QT_CONC_BRANCA", "QT_CONC_PRETA", "QT_CONC_PARDA",
        "QT_CONC_AMARELA", "QT_CONC_INDIGENA", "QT_CONC_CORND",
        "QT_SIT_TRANCADA", "QT_SIT_DESVINCULADO",
        "QT_SIT_TRANSFERIDO", "QT_SIT_FALECIDO",
    ]

    agg_dict = {
        "NU_ANO_CENSO": "min",
        "CO_IES": "min",
        "NO_CURSO": "first",
        "TP_GRAU_ACADEMICO": "first",
        "TP_MODALIDADE_ENSINO": "first",
        "IN_GRATUITO": "first",
        "TP_REDE": "first",
        "CO_CINE_ROTULO": "first",
        "NO_CINE_ROTULO": "first",
    }
    grupos = censo_f.groupby("CO_CURSO")
    medidas = grupos[cols_soma].sum(min_count=1).where(
        grupos[cols_soma].count().eq(grupos.size(), axis=0)
    )
    censo_grp = grupos.agg(agg_dict).join(medidas).reset_index()
    presencial = censo_f.loc[censo_f["TP_DIMENSAO"] == 1].groupby("CO_CURSO")["SG_UF"]
    uf_presencial = presencial.first().where(presencial.nunique(dropna=False).eq(1))
    censo_grp["SG_UF"] = censo_grp["CO_CURSO"].map(uf_presencial)
    censo_grp = censo_grp.rename(columns={
        "CO_IES": "co_ies_censo",
        "QT_ING_FEM": "qt_ing_fem_censo",
        "QT_ING_MASC": "qt_ing_masc_censo",
        "QT_ING_BRANCA": "qt_ing_branca_censo",
        "QT_ING_PRETA": "qt_ing_preta_censo",
        "QT_ING_PARDA": "qt_ing_parda_censo",
        "QT_ING_AMARELA": "qt_ing_amarela_censo",
        "QT_ING_INDIGENA": "qt_ing_indigena_censo",
        "QT_ING_CORND": "qt_ing_cornd_censo",
        "QT_MAT_FEM": "qt_mat_fem_censo",
        "QT_MAT_MASC": "qt_mat_masc_censo",
        "QT_MAT_BRANCA": "qt_mat_branca_censo",
        "QT_MAT_PRETA": "qt_mat_preta_censo",
        "QT_MAT_PARDA": "qt_mat_parda_censo",
        "QT_MAT_AMARELA": "qt_mat_amarela_censo",
        "QT_MAT_INDIGENA": "qt_mat_indigena_censo",
        "QT_MAT_CORND": "qt_mat_cornd_censo",
        "QT_CONC_FEM": "qt_conc_fem_censo",
        "QT_CONC_MASC": "qt_conc_masc_censo",
        "QT_CONC_BRANCA": "qt_conc_branca_censo",
        "QT_CONC_PRETA": "qt_conc_preta_censo",
        "QT_CONC_PARDA": "qt_conc_parda_censo",
        "QT_CONC_AMARELA": "qt_conc_amarela_censo",
        "QT_CONC_INDIGENA": "qt_conc_indigena_censo",
        "QT_CONC_CORND": "qt_conc_cornd_censo",
    })
    censo_grp.columns = [c.lower() for c in censo_grp.columns]

    try:
        enade = pd.read_csv(enade_path, sep=";", encoding="utf-8")
    except UnicodeDecodeError:
        enade = pd.read_csv(enade_path, sep=";", encoding="cp1252")

    enade = enade[enade["NU_ANO"] == 2023].copy()
    enade = enade.rename(columns={
        "NU_ANO": "nu_ano_enade",
        "CO_IES": "co_ies_enade",
        "CO_UF_CURSO": "uf_curso_enade",
    })
    enade.columns = [c.lower() for c in enade.columns]

    # LEFT JOIN para preservar todos os cursos Tecnólogos e demais cursos da Área 1
    df = pd.merge(censo_grp, enade, on="co_curso", how="left", validate="one_to_one")
    df["possui_enade_2023"] = df["nu_ano_enade"].notna()
    df["mesma_ies"] = np.where(
        df["possui_enade_2023"],
        df["co_ies_censo"].astype(str) == df["co_ies_enade"].fillna(-1).astype(int).astype(str),
        np.nan,
    )

    cols_enade_int = [
        "qt_participantes", "qt_notas_validas", "qt_sexo_f", "qt_sexo_m",
        "qt_raca_branca", "qt_raca_preta", "qt_raca_parda",
        "qt_raca_amarela", "qt_raca_indigena",
        "qt_raca_nao_declara", "qt_raca_sem_resposta",
    ]
    for col in cols_enade_int:
        if col in df.columns:
            df[col] = df[col].where(df["possui_enade_2023"], 0)

    return df


COLUNAS_FILTRO = ("grau_academico", "modalidade_ensino", "rede_ensino", "uf_final", "no_cine_rotulo")


def soma_completa(valores):
    """Não trata lacunas em medidas obrigatórias como zeros."""
    return valores.sum(skipna=False, min_count=1)


def dividir(numerador, denominador):
    if isinstance(denominador, pd.Series):
        return numerador / denominador.where(denominador > 0)
    if pd.isna(denominador) or denominador <= 0 or pd.isna(numerador):
        return np.nan
    return numerador / denominador


def percentual(numerador, denominador):
    return dividir(100.0 * numerador, denominador)


def formatar_decimal(valor):
    return "—" if pd.isna(valor) else f"{valor:.1f}".replace(".", ",")


def formatar_percentual(valor):
    return "—" if pd.isna(valor) else f"{formatar_decimal(valor)}%"


def preparar_filtros(df):
    df = df.copy()
    df["grau_academico"] = df["tp_grau_academico"].map(GRAU_MAP).fillna("Outro / Não definido")
    df["modalidade_ensino"] = df["tp_modalidade_ensino"].map(MODALIDADE_CENSO_MAP).fillna("Não informada")
    df["rede_ensino"] = df["tp_rede"].map(REDE_MAP).fillna("Não informada")
    df["no_cine_rotulo"] = df["no_cine_rotulo"].replace("", np.nan).fillna("Não informado")
    # A view pode preencher sg_uf com a UF ENADE quando co_modalidade == 0.
    # Nesse caso a UF de oferta do Censo não está disponível na view.
    presencial = df["modalidade_ensino"].eq("Presencial") & df["co_modalidade"].ne(0)
    df["uf_final"] = df["sg_uf"].astype("string").where(presencial).replace("", np.nan).fillna("UF indisponível")
    df.loc[df["modalidade_ensino"].eq("EaD"), "uf_final"] = "EaD · UF não atribuída"
    return df


def filtrar_cursos(df, selecoes, somente_enade=False):
    mask = pd.Series(True, index=df.index)
    for coluna, valores in zip(COLUNAS_FILTRO, selecoes, strict=True):
        mask &= df[coluna].isin(valores)
    if somente_enade:
        mask &= df["possui_enade_2023"].fillna(False)
    return df.loc[mask].copy()


def pesos_enade(df):
    notas = df["media_nt_ger"]
    quantidades = df["qt_notas_validas"]
    valido = df["possui_enade_2023"].fillna(False) & notas.between(0, 100) & quantidades.gt(0)
    pesos = quantidades.where(valido, 0)
    return notas.where(valido, 0) * pesos, pesos


def indicadores_principais(df):
    cursos = df["co_curso"].nunique()
    cobertura = df.loc[df["possui_enade_2023"].fillna(False), "co_curso"].nunique()
    matr = soma_completa(df["qt_mat"])
    declaradas = matr - soma_completa(df["qt_mat_cornd_censo"])
    preta_parda = soma_completa(df["qt_mat_preta_censo"] + df["qt_mat_parda_censo"])
    desv = soma_completa(df["qt_sit_desvinculado"])
    situacoes = matr + desv + sum(soma_completa(df[col]) for col in (
        "qt_sit_trancada", "qt_sit_transferido", "qt_sit_falecido",
    ))
    notas, pesos = pesos_enade(df)
    return {
        "cursos": cursos,
        "tecnologicos": df.loc[df["grau_academico"].eq("Tecnológico"), "co_curso"].nunique(),
        "cursos_enade": cobertura,
        "cobertura": percentual(cobertura, cursos),
        "matriculas": matr,
        "feminino": percentual(soma_completa(df["qt_mat_fem_censo"]), matr),
        "preta_parda": percentual(preta_parda, declaradas),
        "desvinculacao": percentual(desv, situacoes),
        "media_enade": dividir(notas.sum(), pesos.sum()),
    }


def obter_dados(preferir_local: bool, config, exige_postgres: bool):
    raiz = Path(__file__).resolve().parents[1]
    if preferir_local and not exige_postgres:
        df = carregar_via_csv_local(raiz)
        if df is not None:
            return df, "CSVs Locais (data/processed/)"
    if exige_postgres or any(config[chave] for chave in CAMPOS_POSTGRES):
        try:
            with st.spinner("Consultando PostgreSQL..."):
                carregar = carregar_via_aiven if exige_postgres else carregar_postgres_cache
                df = carregar(config)
            return df, "PostgreSQL (vw_observatorio_censo_enade)"
        except Exception as exc:
            logger.warning(
                "Consulta PostgreSQL indisponível (tipo=%s, sqlstate=%s)",
                type(exc).__name__, getattr(exc, "pgcode", None),
            )
            if exige_postgres:
                return None, None
            st.sidebar.warning("PostgreSQL indisponível. Tentando carregar os CSVs locais.")
    df = carregar_via_csv_local(raiz)
    if df is not None:
        return df, "CSVs Locais (data/processed/)"
    return None, None


st.markdown("""
<header class="observatorio-hero">
  <p class="observatorio-contexto">Área 1 · ODS 5 e ODS 18</p>
  <h1>Observatório de Evasão e Retenção</h1>
  <p>Perfis dos cursos de Exatas, Engenharia e Tecnologia</p>
  <p>Censo da Educação Superior 2024 · ENADE 2023</p>
</header>
""", unsafe_allow_html=True)

st.sidebar.header("Filtros e fonte")
try:
    config = ler_configuracao()
    modo = (config["APP_DATA_MODE"] or "auto").strip().lower()
    if modo not in ("auto", "postgres", "csv"):
        raise ValueError("Modo de dados inválido")
except Exception as exc:
    logger.warning("Configuração do dashboard indisponível (tipo=%s)", type(exc).__name__)
    st.error("A configuração do painel está indisponível. Informe a equipe responsável.")
    st.stop()

exige_postgres = modo == "postgres"
preferir_local = st.sidebar.checkbox("Forçar leitura dos CSVs locais", value=False) if modo == "auto" else False
if modo == "csv":
    # Modo de avaliação: nunca abre conexão remota nem usa fallback PostgreSQL.
    df = carregar_via_csv_local(Path(__file__).resolve().parents[1])
    fonte = "CSVs Locais (data/processed/)" if df is not None else None
else:
    df, fonte = obter_dados(preferir_local, config, exige_postgres)

if df is None and exige_postgres:
    st.error("PostgreSQL indisponível no modo de publicação. Informe a equipe responsável.")
    st.stop()
if df is None:
    st.error(
        "Nenhuma fonte de dados encontrada! Para rodar localmente:\n"
        "1. Coloque os dois arquivos `.csv` ou `.csv.gz` (Censo e ENADE) em `data/processed/`, OU\n"
        "2. Configure suas credenciais do PostgreSQL Aiven no arquivo `.env`."
    )
    st.stop()

st.sidebar.caption(f"Origem dos dados: {fonte}")

df = preparar_filtros(df)

# Filtros na barra lateral
graus = sorted(df["grau_academico"].dropna().unique())
sel_grau = st.sidebar.multiselect(
    "Grau Acadêmico",
    graus,
    default=graus,
    help="Inclui Tecnológico (ADS, Ciência de Dados, Redes, etc.), Bacharelado e Licenciatura.",
)

modalidades = sorted(df["modalidade_ensino"].dropna().unique())
sel_mod = st.sidebar.multiselect("Modalidade", modalidades, default=modalidades)

redes = sorted(df["rede_ensino"].dropna().unique())
sel_rede = st.sidebar.multiselect("Rede de Ensino", redes, default=redes)

ufs = sorted(df["uf_final"].dropna().unique())
areas = sorted(df["no_cine_rotulo"].dropna().unique())
with st.sidebar.expander("UF e área Cine"):
    sel_uf = st.multiselect(
        "UF de oferta (presencial)", ufs, default=ufs,
        help="A UF é a de oferta presencial no Censo. Os cursos EaD ficam em uma categoria própria, "
             "pois seus totais agregados podem incluir vários estados.",
    )
    sel_area = st.multiselect("Área CINE", areas, default=areas)

somente_enade = st.sidebar.checkbox(
    "Apenas cursos com registro no ENADE 2023",
    value=False,
    help="Mantém apenas cursos com registro correspondente no arquivo ENADE 2023.",
)

df_f = filtrar_cursos(df, (sel_grau, sel_mod, sel_rede, sel_uf, sel_area), somente_enade)

filtros_ativos = []
for label, selecionados, disponiveis in (
    ("Grau", sel_grau, graus), ("Modalidade", sel_mod, modalidades), ("Rede", sel_rede, redes),
    ("UF", sel_uf, ufs), ("Cine", sel_area, areas),
):
    if len(selecionados) != len(disponiveis):
        if not selecionados:
            detalhe = "nenhuma opção"
        elif len(selecionados) <= 2:
            detalhe = ", ".join(selecionados)
        else:
            detalhe = f"{len(selecionados)} opções selecionadas"
        filtros_ativos.append(f"{label} · {detalhe}")
if somente_enade:
    filtros_ativos.append("Somente cursos com ENADE 2023")
st.caption(
    f"**Fonte ativa** · {fonte}  \n"
    "**Recorte** · "
    + (" | ".join(filtros_ativos) if filtros_ativos else "Todas as opções dos filtros")
)

if df_f.empty:
    st.warning("Nenhum curso encontrado com os filtros selecionados.")
    st.caption("Amplie as opções na barra lateral para atualizar o recorte.")
    st.stop()

# Os valores e os estados seguem o resultado calculado na Etapa 5A.
kpis = indicadores_principais(df_f)
cartoes = [
    ("cursos", "Cursos no recorte", f"{kpis['cursos']:,}".replace(",", "."),
     f"{kpis['tecnologicos']} tecnológicos · Censo 2024",
     "Número de códigos de curso distintos após os filtros."),
    ("matriculas", "Matrículas", "—" if pd.isna(kpis["matriculas"]) else
     f"{int(kpis['matriculas']):,}".replace(",", "."), "Censo 2024",
     "Soma de QT_MAT, que reúne os vínculos em situação cursando ou formado."),
    ("feminino", "Matrículas femininas", formatar_percentual(kpis["feminino"]), "ODS 5 · Censo 2024",
     "Matrículas do sexo feminino divididas por todas as matrículas do recorte."),
    ("preta_parda", "Matrículas pretas ou pardas", formatar_percentual(kpis["preta_parda"]),
     "ODS 18 · Censo 2024",
     "Matrículas pretas e pardas divididas pelas matrículas com raça/cor declarada."),
    ("desvinculacao", "Composição de desvinculação", formatar_percentual(kpis["desvinculacao"]),
     "Situações de vínculo · Censo 2024",
     "Desvinculados divididos pela soma de matrículas, trancados, desvinculados, transferidos e falecidos."),
    ("media_enade", "Média geral ENADE", formatar_decimal(kpis["media_enade"]),
     "Ponderada pelas notas válidas · ENADE 2023",
     "Médias de curso ponderadas pelo número de notas válidas. "
     "A cobertura conta também os cursos presentes no ENADE sem nota válida."),
]

with st.container(key="cartoes_observatorio"):
    for inicio in (0, 3):
        for coluna, (identificador, label, valor, contexto, ajuda) in zip(
            st.columns(3), cartoes[inicio:inicio + 3], strict=True,
        ):
            dado = kpis[identificador]
            if pd.isna(dado):
                estado = "ausente"
                contexto = "Sem notas válidas" if identificador == "media_enade" else "Dados insuficientes"
            else:
                estado = "zero" if dado == 0 else "valido"
            with coluna.container(key=f"kpi_{estado}_{identificador}", gap="xxsmall"):
                st.metric(label, valor, help=ajuda)
                st.caption(contexto)
st.caption(
    f"**Cobertura ENADE 2023** · {kpis['cursos_enade']} de {kpis['cursos']} cursos "
    f"({formatar_percentual(kpis['cobertura'])}). Cobertura indica presença no arquivo do exame. "
    "A média considera somente cursos com notas válidas."
)

with st.expander("Como interpretar os indicadores"):
    st.markdown(
        "- **Fontes.** O Censo 2024 descreve vínculos acadêmicos e o ENADE 2023 registra o desempenho "
        "em outra edição e população. A associação é por código de curso.\n"
        "- **Composição.** A participação feminina usa todas as matrículas. A participação preta e parda "
        "usa as matrículas com raça/cor declarada. A desvinculação descreve as situações anuais de vínculo.\n"
        "- **Limites.** Ingressantes, matrículas e concluintes são populações observadas no mesmo ano. "
        "Os dados agregados não identificam transições de coorte ou cruzamentos individuais de sexo e raça/cor.\n"
        "- **Disponibilidade.** Zero indica valor observado. Um traço ou uma célula vazia indica base insuficiente."
    )

tab_panorama, tab_intersec, tab_transparencia = st.tabs([
    "Panorama",
    "Perfis dos cursos",
    "Qualidade",
])

with tab_panorama:
    # 1. Comparativo por Grau Acadêmico (Tecnólogo vs. Bacharelado vs. Licenciatura)
    st.subheader("Panorama por grau acadêmico")
    grau_df = (
        df_f.groupby("grau_academico", as_index=False)
        .agg(
            Cursos=("co_curso", "nunique"),
            Cursos_ENADE_2023=("possui_enade_2023", soma_completa),
            Matrículas=("qt_mat", soma_completa),
            Concluintes=("qt_conc", soma_completa),
            fem=("qt_mat_fem_censo", soma_completa),
            negra=("qt_mat_preta_censo", soma_completa),
            parda=("qt_mat_parda_censo", soma_completa),
            cornd=("qt_mat_cornd_censo", soma_completa),
            desv=("qt_sit_desvinculado", soma_completa),
            tranc=("qt_sit_trancada", soma_completa),
            transf=("qt_sit_transferido", soma_completa),
            falec=("qt_sit_falecido", soma_completa),
        )
    )
    grau_df["Cursos_ENADE_2023"] = grau_df["Cursos_ENADE_2023"].astype("Int64")
    grau_df["% Feminino"] = percentual(grau_df["fem"], grau_df["Matrículas"]).round(1)
    decl_g = grau_df["Matrículas"] - grau_df["cornd"]
    grau_df["% Preta/parda entre declaradas"] = percentual(grau_df["negra"] + grau_df["parda"], decl_g).round(1)
    tot_sit_g = (
        grau_df["Matrículas"] + grau_df["desv"] + grau_df["tranc"] + grau_df["transf"] + grau_df["falec"]
    )
    grau_df["% Desvinculado"] = percentual(grau_df["desv"], tot_sit_g).round(1)
    grau_df["% Trancada"] = percentual(grau_df["tranc"], tot_sit_g).round(1)

    panorama = grau_df[
        [
            "grau_academico", "Cursos", "Cursos_ENADE_2023", "Matrículas",
            "Concluintes", "% Feminino", "% Preta/parda entre declaradas",
            "% Desvinculado", "% Trancada",
        ]
    ].rename(columns={"grau_academico": "Grau Acadêmico", "Cursos_ENADE_2023": "Cursos c/ ENADE 2023"})
    st.dataframe(
        panorama.style.format(formatar_percentual, subset=[
            "% Feminino", "% Preta/parda entre declaradas", "% Desvinculado", "% Trancada",
        ]),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "A cobertura indica presença no arquivo ENADE 2023, incluindo cursos sem notas válidas. "
        "Os dados do Censo abrangem todos os cursos que atendem aos filtros."
    )

    st.divider()

    # 2. Composição das populações do Censo
    st.subheader("Composição por população")
    st.caption(
        "Compara ingressantes, matrículas e concluintes como três populações de 2024. "
        "As diferenças de composição não medem transições individuais."
    )

    funil_rows = []
    for etapa, col_tot, col_fem, col_preta, col_parda, col_cornd in [
        ("Ingressantes", "qt_ing", "qt_ing_fem_censo", "qt_ing_preta_censo", "qt_ing_parda_censo", "qt_ing_cornd_censo"),
        ("Matriculados", "qt_mat", "qt_mat_fem_censo", "qt_mat_preta_censo", "qt_mat_parda_censo", "qt_mat_cornd_censo"),
        ("Concluintes", "qt_conc", "qt_conc_fem_censo", "qt_conc_preta_censo", "qt_conc_parda_censo", "qt_conc_cornd_censo"),
    ]:
        tot = soma_completa(df_f[col_tot])
        fem = soma_completa(df_f[col_fem])
        negra = soma_completa(df_f[col_preta] + df_f[col_parda])
        cornd = soma_completa(df_f[col_cornd])
        decl = tot - cornd
        funil_rows.append({
            "Etapa": etapa,
            "Total": tot,
            "% Feminino": round(percentual(fem, tot), 1),
            "% Preta/parda entre declaradas": round(percentual(negra, decl), 1),
            "% Raça Não Informada": round(percentual(cornd, tot), 1),
        })

    df_funil = pd.DataFrame(funil_rows)
    rotulos_composicao = {
        "% Feminino": "Feminino",
        "% Preta/parda entre declaradas": "Preta/parda · declaradas",
        "% Raça Não Informada": "Raça/cor não informada",
    }
    composicao = df_funil.rename(columns=rotulos_composicao).melt(
        id_vars="Etapa", value_vars=list(rotulos_composicao.values()),
        var_name="Indicador", value_name="Percentual",
    )
    composicao["Etapa"] = composicao["Etapa"].replace({"Matriculados": "Matrículas"})
    fig_funil = px.bar(
        composicao, x="Etapa", y="Percentual", color="Indicador",
        color_discrete_map={
            "Feminino": "#167D8D", "Preta/parda · declaradas": "#A26D17",
            "Raça/cor não informada": "#51718F",
        },
        barmode="group",
        category_orders={"Etapa": ["Ingressantes", "Matrículas", "Concluintes"]},
    )
    fig_funil.update_traces(hovertemplate="<b>%{fullData.name}</b><br>%{x}: %{y:.1f}%<extra></extra>")
    fig_funil.update_layout(
        template="plotly_white", height=355, separators=",.",
        xaxis_title=None, yaxis_title=None, legend_title_text="",
        legend=dict(orientation="h", y=-0.2, x=0),
        margin=dict(l=15, r=14, t=20, b=95),
    )
    fig_funil.update_yaxes(range=[0, 100], ticksuffix="%", gridcolor="#E5EDF2", fixedrange=True)
    fig_funil.update_xaxes(tickangle=0, fixedrange=True)
    st.plotly_chart(fig_funil, width="stretch", theme=None, config={"displayModeBar": False})
    with st.expander("Consultar percentuais e totais da composição"):
        st.dataframe(
            df_funil.style.format(formatar_percentual, subset=list(rotulos_composicao)),
            width="stretch", hide_index=True,
        )

    st.divider()

with tab_intersec:
    # 3. Matriz de perfis agregados
    st.subheader("Matriz de perfis dos cursos")
    st.caption(
        "Considera cursos com pelo menos 30 matrículas e pelo menos uma matrícula com raça/cor declarada. "
        "Os eixos representam duas proporções separadas por curso. A interseção individual é desconhecida."
    )

    perfil = df_f[df_f["qt_mat"] >= 30].copy()
    perfil["total_situacoes"] = (
        perfil["qt_mat"]
        + perfil["qt_sit_trancada"]
        + perfil["qt_sit_desvinculado"]
        + perfil["qt_sit_transferido"]
        + perfil["qt_sit_falecido"]
    )
    perfil["pct_fem"] = percentual(perfil["qt_mat_fem_censo"], perfil["qt_mat"])
    perfil["pct_negra"] = percentual(
        perfil["qt_mat_preta_censo"] + perfil["qt_mat_parda_censo"],
        perfil["qt_mat"] - perfil["qt_mat_cornd_censo"],
    )
    perfil = perfil.dropna(subset=["pct_fem", "pct_negra"]).copy()

    perfil["Faixa Feminino"] = np.select(
        [perfil["pct_fem"] < 10, perfil["pct_fem"] <= 20],
        ["1) fem. < 10%", "2) fem. 10-20%"],
        default="3) fem. > 20%",
    )
    perfil["Faixa Preta/Parda"] = np.select(
        [perfil["pct_negra"] < 25, perfil["pct_negra"] <= 50],
        ["1) preta/parda < 25%", "2) preta/parda 25-50%"],
        default="3) preta/parda > 50%",
    )

    if perfil.empty:
        st.info("Sem cursos elegíveis para a matriz com os filtros atuais.")
    else:
        perfil["nota_x_validas"], perfil["peso_nota"] = pesos_enade(perfil)
        matriz = (
            perfil.groupby(["modalidade_ensino", "Faixa Feminino", "Faixa Preta/Parda"], as_index=False)
            .agg(
                Cursos=("co_curso", "count"),
                Matrículas=("qt_mat", soma_completa),
                Concluintes=("qt_conc", soma_completa),
                desv=("qt_sit_desvinculado", soma_completa),
                tranc=("qt_sit_trancada", soma_completa),
                tot_sit=("total_situacoes", soma_completa),
                soma_nota=("nota_x_validas", "sum"),
                soma_validas=("peso_nota", "sum"),
            )
        )
        matriz["% Desvinculado"] = percentual(matriz["desv"], matriz["tot_sit"]).round(1)
        matriz["% Trancada"] = percentual(matriz["tranc"], matriz["tot_sit"]).round(1)
        matriz["Nota ENADE Média"] = dividir(matriz["soma_nota"], matriz["soma_validas"]).round(1)

        exibir_matriz = matriz[
            ["modalidade_ensino", "Faixa Feminino", "Faixa Preta/Parda", "Cursos", "Matrículas", "Concluintes", "% Desvinculado", "% Trancada", "Nota ENADE Média"]
        ]
        ordem_fem = ["1) fem. < 10%", "2) fem. 10-20%", "3) fem. > 20%"]
        ordem_negra = ["1) preta/parda < 25%", "2) preta/parda 25-50%", "3) preta/parda > 50%"]
        fig_matriz = px.density_heatmap(
            perfil,
            x="Faixa Feminino",
            y="Faixa Preta/Parda",
            facet_col="modalidade_ensino",
            facet_col_wrap=1,
            facet_row_spacing=.17,
            category_orders={
                "Faixa Feminino": ordem_fem,
                "Faixa Preta/Parda": ordem_negra,
                "modalidade_ensino": ["Presencial", "EaD"],
            },
            text_auto=True,
            color_continuous_scale=["#EAF2F5", "#7BC4C3", "#167D8D", "#17324D"],
            labels={"count": "Cursos", "Faixa Feminino": "% feminino", "Faixa Preta/Parda": "% preta/parda"},
        )
        fig_matriz.update_layout(
            template="plotly_white",
            height=530 if perfil["modalidade_ensino"].nunique() > 1 else 300,
            coloraxis_colorbar=dict(title="Cursos", thickness=10, len=.75),
            separators=",.",
            margin=dict(l=12, r=12, t=34, b=35),
        )
        fig_matriz.for_each_annotation(lambda annotation: annotation.update(
            text=annotation.text.split("=", 1)[-1], font=dict(color="#17324D", size=13),
        ))
        fig_matriz.update_xaxes(tickvals=ordem_fem, ticktext=["<10%", "10–20%", ">20%"],
                                tickangle=0, title_text="% feminino", showticklabels=True, fixedrange=True)
        fig_matriz.update_yaxes(tickvals=ordem_negra, ticktext=["<25%", "25–50%", ">50%"],
                                title_text="% preta/parda", fixedrange=True)
        st.plotly_chart(fig_matriz, width="stretch", theme=None, config={"displayModeBar": False})
        st.dataframe(
            exibir_matriz.rename(columns={"modalidade_ensino": "Modalidade"}).style.format({
                "% Desvinculado": formatar_percentual,
                "% Trancada": formatar_percentual,
                "Nota ENADE Média": formatar_decimal,
            }),
            width="stretch",
            hide_index=True,
        )

    st.divider()

with tab_transparencia:
    # 4. Transparência: Raça Declarada vs. Não Declarada
    st.subheader("Declaração de raça/cor")
    st.caption(
        "Os denominadores são as matrículas do Censo 2024 e os registros do ENADE 2023. "
        "As colunas do ENADE ficam vazias quando o grupo não tem registros para calcular o indicador."
    )

    transp = (
        df_f.groupby(["grau_academico", "modalidade_ensino"], as_index=False)
        .agg(
            matriculas=("qt_mat", soma_completa),
            cornd_censo=("qt_mat_cornd_censo", soma_completa),
            part_enade=("qt_participantes", soma_completa),
            nd_enade=("qt_raca_nao_declara", soma_completa),
            sr_enade=("qt_raca_sem_resposta", soma_completa),
        )
    )

    transp["Declarada (Censo)"] = (transp["matriculas"] - transp["cornd_censo"]).astype("Int64")
    transp["Não Informada (Censo)"] = transp["cornd_censo"].astype("Int64")
    transp["% Não Informada (Censo)"] = percentual(transp["cornd_censo"], transp["matriculas"]).round(1)

    tem_registros = transp["part_enade"] > 0
    nao_decl_enade = transp["nd_enade"] + transp["sr_enade"]
    transp["Declarada (ENADE)"] = (transp["part_enade"] - nao_decl_enade).where(tem_registros).astype("Int64")
    transp["Não Declara / Sem Resp. (ENADE)"] = nao_decl_enade.where(tem_registros).astype("Int64")
    transp["% Não Declara / Sem Resp. (ENADE)"] = percentual(nao_decl_enade, transp["part_enade"]).round(1)

    qualidade = transp[
        [
            "grau_academico", "modalidade_ensino", "Declarada (Censo)", "Não Informada (Censo)",
            "% Não Informada (Censo)", "Declarada (ENADE)", "Não Declara / Sem Resp. (ENADE)",
            "% Não Declara / Sem Resp. (ENADE)",
        ]
    ].rename(columns={"grau_academico": "Grau Acadêmico", "modalidade_ensino": "Modalidade"})
    st.dataframe(
        qualidade.style.format(formatar_percentual, subset=[
            "% Não Informada (Censo)", "% Não Declara / Sem Resp. (ENADE)",
        ]),
        width="stretch",
        hide_index=True,
    )
