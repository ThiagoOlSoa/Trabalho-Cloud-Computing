"""Gera o JSON importável a partir de consultas SQL revisáveis."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "dashboard_observatorio.json"
DATASOURCE = {"type": "grafana-postgresql-datasource", "uid": "${DS_POSTGRESQL}"}
COLORS = ("#167D8D", "#A26D17")
DEMOGRAPHIC_FIELDS = ("Feminina (%)", "Preta/parda (%)")
VARIABLES = (
    ("grau", "Grau acadêmico", "grau_academico"),
    ("modalidade", "Modalidade", "modalidade_ensino"),
    ("rede", "Rede de ensino", "rede_ensino"),
    ("uf", "UF de oferta presencial", "uf_oferta"),
    ("cine", "Área Cine", "area_cine"),
)


def sql(name):
    return (ROOT / "queries" / f"{name}.sql").read_text(encoding="utf-8").strip()


def scope(filtered=True):
    common = sql("cursos")
    return common + sql("recorte") if filtered else common


def options_query(column):
    return f"{scope(False)}\nSELECT DISTINCT {column} FROM cursos ORDER BY {column}"


def query(name, group=None):
    body = sql(name)
    if group:
        body = body.replace("{{grupo}}", dict(por_grau="grau_academico", por_modalidade="modalidade_ensino")[group])
    return scope() + "\n" + body


def stat_query(name, fields):
    body = sql(name)
    projection = []
    for field, label, unit in fields:
        if unit == "integer":
            formatted = f"""translate(to_char({field}, 'FM999,999,999,990'), ',', '.')"""
        else:
            formatted = f"""replace(to_char({field}, 'FM990.0'), '.', ',')"""
            if unit == "pct":
                formatted += " || '%'"
        projection.append(f'{formatted} AS "{label}"')
    return f"{scope()},\nmedidas AS (\n{body}\n)\nSELECT " + ",\n       ".join(projection) + "\nFROM medidas"


def panel(panel_id, kind, title, position, description=""):
    x, y, width, height = position
    return {
        "id": panel_id, "type": kind, "title": title, "description": description,
        "gridPos": {"x": x, "y": y, "w": width, "h": height}, "transparent": kind == "text",
    }


def data_panel(result, statement, defaults, options, overrides=()):
    return {
        **result, "datasource": DATASOURCE,
        "targets": [{"refId": "A", "datasource": DATASOURCE, "editorMode": "code",
                     "format": "table", "rawQuery": True, "rawSql": statement}],
        "fieldConfig": {"defaults": {"noValue": "—", **defaults}, "overrides": list(overrides)},
        "options": options,
    }


def text(panel_id, title, position, content):
    return {**panel(panel_id, "text", title, position),
            "options": {"mode": "markdown", "content": content}}


def stats(panel_id, title, position, source, fields, description):
    text_size = {"text": {"titleSize": 13, "valueSize": 27}} if len(fields) == 2 else {}
    return data_panel(
        panel(panel_id, "stat", title, position, description),
        stat_query(source, fields),
        {"color": {"mode": "fixed", "fixedColor": "#3596A1"}},
        {"colorMode": "value", "graphMode": "none", "orientation": "auto",
         "justifyMode": "center", "textMode": "value_and_name", "wideLayout": False,
         "reduceOptions": {"values": False, "calcs": ["lastNotNull"], "fields": "/.*/"},
         **text_size},
    )


def override(field, **properties):
    return {"matcher": {"id": "byName", "options": field},
            "properties": [{"id": key, "value": value} for key, value in properties.items()]}


def comparison(panel_id, title, position, group):
    return data_panel(
        panel(panel_id, "barchart", title, position,
              "Participação feminina no total de matrículas e participação preta/parda entre matrículas com raça/cor declarada."),
        query("comparacoes", group),
        {"unit": "locale", "decimals": 1, "min": 0, "max": 100, "color": {"mode": "palette-classic"}},
        {"xField": "Categoria", "orientation": "horizontal", "stacking": "none",
         "groupWidth": 0.72, "barWidth": 0.82, "fillOpacity": 87,
         "legend": {"showLegend": True, "displayMode": "list", "placement": "bottom"},
         "tooltip": {"mode": "multi", "sort": "none"}, "showValue": "never"},
        [override(field, color={"mode": "fixed", "fixedColor": color})
         for field, color in zip(DEMOGRAPHIC_FIELDS, COLORS, strict=True)],
    )


def table(panel_id, title, position, source, description, percentages, min_width):
    overrides = [override(field, unit="locale", decimals=1) for field in percentages]
    if source == "perfis":
        overrides.append(override("Média ENADE", unit="locale", decimals=1))
    return data_panel(
        panel(panel_id, "table", title, position, description),
        query(source), {"custom": {"minWidth": min_width}},
        {"showHeader": True, "cellHeight": "md", "footer": {"show": False}},
        overrides,
    )


def variables():
    all_options = {"text": "All", "value": "$__all"}
    result = [
        {"name": name, "label": label, "type": "query", "datasource": DATASOURCE,
         "query": options_query(column), "definition": options_query(column),
         "refresh": 1, "multi": True, "includeAll": True, "sort": 0,
         "current": {"text": ["All"], "value": ["$__all"]}, "options": [all_options]}
        for name, label, column in VARIABLES
    ]
    enade_options = (("Todos", "Todos"), ("Apenas com registro", "Com registro"))
    result.append({
        "name": "enade", "label": "ENADE 2023", "type": "custom",
        "query": "Todos,Apenas com registro : Com registro",
        "includeAll": False, "multi": False,
        "current": {"text": "Todos", "value": "Todos"},
        "options": [{"text": text, "value": value, "selected": value == "Todos"}
                    for text, value in enade_options],
    })
    return result


def dashboard():
    return {
        "__inputs": [{"name": "DS_POSTGRESQL", "label": "PostgreSQL do Observatório",
                      "type": "datasource", "pluginId": DATASOURCE["type"], "pluginName": "PostgreSQL"}],
        "id": None, "uid": "observatorio-area1", "title": "Observatório de Evasão e Retenção | Área 1",
        "description": "Censo da Educação Superior 2024 e ENADE 2023 · INEP · ODS 5 e 18",
        "tags": ["INEP", "ODS 5", "ODS 18"], "editable": True, "schemaVersion": 41, "version": 1,
        "timezone": "browser", "timepicker": {"hidden": True}, "refresh": "",
        "templating": {"list": variables()},
        "panels": [
            text(1, "", (0, 0, 24, 4),
                 "# Observatório de Evasão e Retenção\n"
                 "**Área 1 · Censo 2024 e ENADE 2023 · INEP · ODS 5 e 18**"),
            stats(2, "Recorte e participação feminina", (0, 4, 12, 5), "indicadores",
                  [("cursos", "Cursos", "integer"), ("matriculas", "Matrículas", "integer"),
                   ("feminino", "Participação feminina", "pct")],
                  "Uma linha por curso do Censo. Participação feminina usa o total de matrículas."),
            stats(3, "Raça/cor, vínculos e desempenho", (12, 4, 12, 5), "indicadores",
                  [("preta_parda", "Preta/parda · declaradas", "pct"),
                   ("desvinculacao", "Desvinculação anual", "pct"),
                   ("media_enade", "Média geral ENADE", "decimal")],
                  "Preta/parda entre matrículas com raça/cor declarada. Desvinculação entre os vínculos do ano. Média ENADE ponderada por notas válidas."),
            stats(4, "Ingressantes e concluintes", (0, 9, 12, 5), "indicadores",
                  [("ingressantes", "Ingressantes", "integer"), ("concluintes", "Concluintes", "integer")],
                  "São populações observadas em 2024, com totais próprios."),
            stats(11, "Cobertura do ENADE 2023", (12, 9, 12, 5), "indicadores",
                  [("cursos_enade", "Cursos com ENADE", "integer"), ("cobertura", "Cobertura ENADE", "pct")],
                  "A cobertura é a proporção de cursos selecionados com registro ENADE 2023, inclusive quando o curso não tem notas válidas."),
            comparison(5, "Participação por grau acadêmico", (0, 14, 12, 10), "por_grau"),
            comparison(6, "Participação por modalidade", (12, 14, 12, 10), "por_modalidade"),
            table(7, "Composição por população do Censo 2024", (0, 24, 16, 7), "populacoes",
                  "Preta/parda entre quem tem raça/cor declarada. Cada população tem seu próprio denominador.",
                  DEMOGRAPHIC_FIELDS, 116),
            stats(8, "Raça/cor sem informação", (16, 24, 8, 7), "declaracao",
                  [("censo", "Matrículas Censo", "pct"), ("enade", "Participantes ENADE", "pct")],
                  "Censo: não declarada ou indisponível. ENADE: não declarou ou sem resposta. Cada fonte usa seu próprio total."),
            table(9, "Perfis agregados dos cursos", (0, 31, 24, 11), "perfis",
                  "Cursos com pelo menos 30 matrículas e base para as duas proporções. As faixas descrevem totais marginais por curso.",
                  ("Desvinculação (%)",), 110),
            text(10, "Como ler os indicadores", (0, 42, 24, 13),
                 "**—** indica medida indisponível.\n\n"
                 "**ODS 5 e 18.** Os percentuais de participação descrevem matrículas. "
                 "As faixas dos perfis combinam proporções por curso. Uma estimativa sobre mulheres negras "
                 "exigiria o cruzamento individual de sexo e raça/cor.\n\n"
                 "**Vínculos no Censo.** A desvinculação é uma composição anual de situações. Uma taxa "
                 "longitudinal exigiria acompanhar coortes. Ingressantes, matriculados e concluintes são "
                 "populações observadas em 2024.\n\n"
                 "**ENADE 2023.** A cobertura mede correspondência por curso. A média usa apenas "
                 "notas válidas. Censo e ENADE têm anos e populações distintos.\n\n"
                 "**UF.** A UF refere-se à oferta presencial do Censo. Os cursos EaD permanecem em "
                 "**EaD · UF não atribuída**, com seus totais nacionais."),
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Confere se o JSON está atualizado.")
    content = json.dumps(dashboard(), ensure_ascii=False, indent=2) + "\n"
    if parser.parse_args().check:
        if OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("JSON desatualizado. Execute python grafana/gerar_dashboard.py.")
    else:
        OUTPUT.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
