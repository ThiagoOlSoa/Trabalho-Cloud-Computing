# CSVs compactados do projeto

A pasta contém os **dois arquivos públicos processados**:

- `censo_2024_area1.csv.gz` — Censo da Educação Superior 2024 (110.022 linhas; 67 colunas), originalmente `cp1252`.
- `enade_2023_area1.csv.gz` — ENADE 2023 agregado (1.665 linhas; 22 colunas), originalmente UTF-8.

O dashboard e os loaders podem ler gzip diretamente. Nas cargas, informe o caminho com `--csv`. A pasta não precisa conter versões `.csv` descompactadas. Não confunda esses arquivos com o resumo `data/indicadores_referencia.csv`.

Para a implantação, consulte [docs/publicacao_csv.md](../../docs/publicacao_csv.md). Não inclua dados brutos ou arquivos de credenciais no GitHub.

A preparação da carga e a ordem de execução estão em [docs/etapa_6c_aiven.md](../../docs/etapa_6c_aiven.md).
