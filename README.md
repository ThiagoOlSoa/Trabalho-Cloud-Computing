# Observatório de Evasão e Retenção

Projeto acadêmico de análise de cursos da Área 1, com foco em Exatas, Engenharia, Tecnologia e Matemática. Usa os microdados oficiais do Censo da Educação Superior 2024 e o agregado do ENADE 2023 pelo código do curso, no contexto dos ODS 5 e 18.

## Indicadores conferidos nos CSVs de referência

Reprocessamos os arquivos completos do **Censo da Educação Superior 2024** (110.022 registros, 7.085 cursos em todas as dimensões geográficas) e do **ENADE 2023 agregado** (1.665 cursos). A visão do dashboard utiliza as dimensões 1 e 2 do Censo, abrangendo **7.078 cursos**; sete cursos presentes apenas na dimensão 3 ficam fora da visão, mas permanecem na base original.

| Indicador (recorte do dashboard) | Valor |
| --- | ---: |
| Cursos | 7.078 |
| Matrículas (Censo 2024) | 1.269.093 |
| Ingressantes (Censo 2024) | 673.375 |
| Concluintes (Censo 2024) | 153.760 |
| Participação feminina nas matrículas | 20,2% |
| Participação preta/parda entre matrículas com raça/cor declarada | 41,2% |
| Composição anual de desvinculação | 21,7% |
| Cursos com ENADE 2023 | 1.665 (23,5%) |
| Média ENADE ponderada pelo número de notas válidas | 41,8 |

A tabela [`data/indicadores_referencia.csv`](data/indicadores_referencia.csv) contém totais verificáveis por modalidade, rede e grau, além do total geral. Esses recortes são alternativas de agrupamento do mesmo universo e não devem ser somados entre si. O ENADE 2023 e o Censo 2024 representam anos/populações distintos; os totais marginais de gênero e raça/cor **não permitem calcular evasão individual de mulheres negras**. A desvinculação mostrada é uma composição anual de vínculos, não uma taxa longitudinal de evasão.

**Dados não versionados:** o repositório publica amostras de 120 linhas e um CSV-resumo, mas **não** contém os dois CSVs processados completos: `data/processed/censo_2024_area1.csv` (~41,8 MB) e `data/processed/enade_2023_area1.csv` (~151 KB). Para executar o fallback CSV, os dois arquivos precisam existir localmente nessa pasta, conforme [guia](data/README.md). Para publicar sem esses arquivos, configurar a Aiven e os Secrets do Streamlit com `APP_DATA_MODE=postgres`. A publicação no GitHub não comprova a conexão ao banco remoto.

## Teste online com CSVs compactados — antes da Aiven

O aplicativo também lê os dois arquivos `.csv.gz` diretamente, sem extraí-los no repositório. Os dados públicos processados não estão todos no GitHub automaticamente: após adicionar os dois arquivos compactados em `data/processed/`, você pode testar a mesma aplicação no Streamlit Community Cloud com `APP_DATA_MODE=csv`, sem credenciais de banco. Esse modo **não consulta a Aiven**, mesmo que existam configurações PostgreSQL.

Veja o [guia de implantação CSV](docs/publicacao_csv.md) e a [pasta de dados compactados](data/processed/README.md) para os nomes exatos, instruções de upload e testes. O modo `auto` e o modo `postgres` continuam disponíveis para o desenvolvimento local e para a integração Aiven futura.

## Execução local

Use Python 3.12 e execute na raiz do projeto.

```sh
python -m venv .venv
# Ative o ambiente virtual antes dos comandos abaixo.
python -m pip install -r requirements.txt
python -m streamlit run app/app.py
```

Para usar CSVs, coloque os dois arquivos processados esperados em `data/processed/`. Os nomes e os comandos de preparação estão no [Guia de dados](data/README.md). As amostras de inspeção em `data/amostras/` têm cobertura parcial.

O modo local `auto` tenta PostgreSQL quando configurado e permite o fallback CSV. Para publicação e demonstração, `APP_DATA_MODE=postgres` exige a origem PostgreSQL e comunica falhas de forma genérica. A configuração aceita ambiente, `.env` local ou a seção `[observatorio]` dos Secrets do Streamlit. Use o usuário de leitura definido pelo responsável pelo serviço. A configuração e a validação de TLS estão no [Manual de publicação](docs/publicacao.md).

## Dados, infraestrutura e validação

- O ETL trata o Censo 2024 e valida o ENADE 2023 já agregado. A reconstrução do agregado ENADE depende dos arquivos brutos e do dicionário da edição. [Guia de dados](data/README.md)
- O PostgreSQL local foi validado com PostgreSQL 16.2, primeira carga, reexecução, rollback e consultas. O esquema novo usa `sql/schema.sql` e `sql/views.sql`. Para bancos existentes, inspecione o esquema e as permissões antes de escolher qualquer migração. [Carga e migrações](docs/carga_postgresql.md)
- A base local de referência tem 7.085 cursos. A view expõe 7.078 cursos das dimensões 1 e 2, dos quais 1.665 têm registro correspondente no ENADE. Sete cursos exclusivos da dimensão 3 seguem armazenados. Os percentuais descrevem composições agregadas de populações distintas. [Fórmulas e limites](docs/indicadores.md)
- O Terraform para o PostgreSQL gratuito da Aiven passou em `fmt`, `init -backend=false` e `validate`. A verificação da configuração e dos dados do serviço real depende de acesso autorizado. [Manual Terraform](terraform/README.md)
- O layout, a leitura em telas estreitas e os estados dos cartões são descritos na [documentação visual](docs/dashboard_visual.md).

Execute `python -m unittest discover -s tests -v`. As variáveis opcionais para os testes PostgreSQL descartáveis e a comparação com os CSVs completos estão nos guias de carga e indicadores. O histórico documental em `docs/Arquitetura.docx` descreve fases anteriores. Use a documentação Markdown como referência operacional.

A versão 6A foi preparada para publicação e testada localmente. O ZIP de entrega inclui um manifesto de integridade. O acesso à Aiven e a publicação no GitHub e no Streamlit Community Cloud ainda dependem de aprovação e validação da equipe. [Relatório de prontidão](docs/prontidao_6a.md)
