# Observatório de Evasão e Retenção

Projeto acadêmico de Computação em Nuvem sobre os cursos da Área 1, com recorte em Exatas, Engenharia, Tecnologia e Matemática. O painel descreve a participação por gênero e raça/cor, a composição anual dos vínculos e o desempenho de cursos, no contexto dos ODS 5 e 18. As fontes oficiais são o Censo da Educação Superior 2024 e o ENADE 2023, ambos do INEP. [Microdados do Censo](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior) · [Microdados do ENADE](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enade)

## Arquitetura e dados

O ETL Python transforma o Censo e valida o agregado ENADE. Os loaders registram cada carga em uma transação, validam os arquivos antes de gravar e permitem reexecução. O PostgreSQL usa dois fatos e dimensões de instituição, curso, Cine e localização. O Streamlit utiliza a consulta SQL por curso, compatível com a chave textual do ENADE legado. O desenho inclui o Aiven PostgreSQL gratuito e Terraform para declaração de infraestrutura. [Diagrama](docs/arquitetura.md) · [Dicionário de variáveis](docs/dicionario_variaveis.md) · [ETL e dados](data/README.md) · [Modelagem e carga](docs/carga_postgresql.md)

Os dois **CSV gzip completos** estão versionados em `data/processed/`. São dados públicos processados. As bases brutas ficam fora do Git. O Censo contém 110.022 registros e 7.085 cursos em todas as dimensões. A camada analítica usa as dimensões 1 e 2, com 7.078 cursos, dos quais 1.665 têm correspondência no ENADE e 5.413 permanecem sem ENADE. Sete cursos que aparecem apenas na dimensão 3 permanecem na base. [Arquivos processados](data/processed/README.md)

| Indicador do recorte integral | Referência |
|---|---:|
| Cursos | 7.078 |
| Matrículas | 1.269.093 |
| Ingressantes | 673.375 |
| Concluintes | 153.760 |
| Participação feminina | 20,2% |
| Participação preta/parda entre matrículas com raça/cor declarada | 41,2% |
| Composição anual de desvinculação | 21,7% |
| Cursos com ENADE | 1.665 |
| Cobertura ENADE | 23,5% |
| Média geral ENADE ponderada por notas válidas | 41,8 |

A matriz compara perfis agregados dos cursos. Os totais marginais não fornecem contagens ou taxas específicas de mulheres negras. Participação, desvinculação anual e cobertura ENADE descrevem medidas diferentes. Uma taxa longitudinal de evasão exige dados de coorte. Censo 2024 e ENADE 2023 descrevem anos e populações distintos. [Fórmulas e limitações](docs/indicadores.md)

## Dashboards e reprodução

O **Streamlit Community Cloud** é a plataforma oficial de visualização e apresentação. A configuração de produção usa `APP_DATA_MODE=postgres` e TLS `verify-full`. O painel exibe seis métricas principais, a cobertura ENADE e seis filtros. Os CSVs versionados servem para reprodução e contingência local identificada. A publicação, a conexão a `defaultdb` e o acesso do professor ainda precisam de homologação. [Publicação e Secrets](docs/publicacao.md) · [Roteiro de dez minutos](docs/apresentacao_final.md)

Na raiz, com Python 3.12 e ambiente virtual ativo:

```sh
python -m pip install -r requirements.txt
APP_DATA_MODE=csv python -m streamlit run app/app.py
```

O modo CSV usa os gzip versionados. Para conectar ao PostgreSQL autorizado, configure `APP_DATA_MODE=postgres`, o usuário de leitura, a CA e TLS `verify-full`. A telemetria informa a fonte da sessão que forneceu os dados. O tempo exibido inclui eventual cache. [Configuração de ambiente e TLS](docs/publicacao.md)

`sql/schema.sql` e `sql/views.sql` são referências para um banco novo, com chave inteira no ENADE. A view antiga na Aiven é um objeto legado e pode conter somente os cursos com ENADE. O dashboard usa `sql/cursos.sql` e dispensa essa view. Para homologação, prefira o preflight de colunas e o verificador de indicadores em modo de leitura. [Preflight](sql/preflight_painel.sql) · [Validador](scripts/validar_indicadores.py)

## Terraform, testes e integridade

O plano declarado é `free-1-1gb`, com provedor `aiven/aiven` e token em variável de ambiente. A demonstração local usa `terraform fmt -check`, `terraform init -backend=false` e `terraform validate`. Essas verificações atestam a configuração. A situação do serviço existente e sua adoção por Terraform exigem revisão do responsável. [Roteiro Terraform](terraform/README.md)

```sh
python -m unittest discover -s tests -v
bash scripts/testar_postgres_local.sh
python -m scripts.manifesto_sha256 --check
sha256sum -c MANIFESTO_SHA256.txt
```

A suíte integrada requer PostgreSQL 16 com `initdb` e `pg_ctl`. Ela cria um cluster descartável por socket Unix, carrega os CSVs completos e testa os esquemas novo e legado. O GitHub Actions executa as duas suítes e informa os testes ignorados. Após adicionar ou atualizar arquivos versionados, execute `git add`, gere o manifesto com `python -m scripts.manifesto_sha256` e inclua o manifesto atualizado no commit. [Workflow de qualidade](.github/workflows/qualidade.yml) · [Conformidade e pendências](docs/conformidade_final.md)
