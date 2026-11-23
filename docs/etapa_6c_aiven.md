# Etapa 6C — Integração com Aiven PostgreSQL (sem Streamlit Cloud)

**Objetivo:** confirmar o serviço PostgreSQL Free já existente, auditar o banco em modo somente leitura, e preparar uma carga controlada dos CSVs oficiais agregados do INEP. **Não há autorização neste roteiro para criar, importar, apagar, migrar ou carregar dados na instância real.**

## 1. Diferença entre serviços

Aiven for PostgreSQL hospeda e gerencia o **banco de dados**, não o dashboard visual do projeto. O **PG Studio** na Console oferece editor SQL, listagem de tabelas e mapa de esquema, suficientes para auditar e demonstrar consultas. O requisito acadêmico de **dashboard online com filtros** continuará pendente até a escolha de uma ferramenta visual; nenhuma publicação em Streamlit Cloud será feita nesta etapa. Aiven Runtime para hospedar aplicação tem cobrança própria (não faz parte do PostgreSQL Free).

Referências:
- [Aiven PostgreSQL Free](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier)
- [PG Studio](https://aiven.io/docs/products/postgresql/howto/pg-studio)
- [Importar recurso Aiven existente no Terraform](https://registry.terraform.io/providers/aiven/aiven/latest/docs/guides/importing-resources)
- [Aiven PostgreSQL somente leitura](https://aiven.io/docs/products/postgresql/howto/readonly-user)

## 2. Informações a confirmar com a equipe

Sem enviar credenciais pelo chat nem salvá-las no GitHub:
- Nome exato do **projeto Aiven** e do **serviço PostgreSQL**.
- Se existe, está RUNNING/ativo e é Free (`free-1-1gb` ou plano gratuito mostrado na conta).
- **Banco de dados** esperado, espaço usado e se há tabelas do observatório.
- Administrador responsável, se já existe Terraform gerenciando o serviço e se há backup recuperável.
- Confirmação de que credenciais antigas compartilhadas foram revogadas/trocadas.

O Free tem **1 GB de armazenamento**, **1 GB RAM**, **1 CPU**, **até 20 conexões** e restrições de serviços por organização. Não ativar plano pago, Aiven Runtime ou Grafana pago para contornar limitações.

## 3. Diagnóstico inicial, sem gravar

1. Responsável abre a [Console Aiven](https://console.aiven.io/) e seleciona o PostgreSQL correto.
2. Confirma plano gratuito, estado, armazenamento e banco, sem expor a senha nem URL que contenha credenciais.
3. No **PG Studio → SQL editor**, executa as instruções SELECT de [`sql/aiven_preflight.sql`](../sql/aiven_preflight.sql). Se o editor não aceitar vários comandos, executar cada SELECT isoladamente.
4. Anota apenas o resultado não sensível: quais tabelas e view existem, tamanho do banco e se já possui dados. Se não existir view, **não execute** o segundo script.
5. Se a view existir e o administrador autorizar leitura, executar [`sql/aiven_validacao_dados.sql`](../sql/aiven_validacao_dados.sql) e comparar os indicadores com o quadro abaixo.
6. Se índices, constraints, migrações ou totais divergirem, documentar o estado e **interromper**: não sobrescrever nem repetir carga automaticamente.

## 4. Valores de referência no banco (Censo 2024 + ENADE 2023)

| Medida | Esperado após carga completa |
| --- | ---: |
| Linhas `fato_censo_curso` | 110.022 |
| Cursos na dimensão de cursos | 7.085 |
| Cursos na view (dimensões 1 e 2) | 7.078 |
| Cursos ENADE na view | 1.665 |
| Matrículas | 1.269.093 |
| Ingressantes | 673.375 |
| Concluintes | 153.760 |
| Participação feminina | 20,2% |
| Pretos/pardos entre declaradas | 41,2% |
| Composição anual de desvinculação | 21,7% |
| Média ENADE ponderada | 41,8 |

Os indicadores são compostos a partir de dados agregados. Não representam taxas individuais de evasão de mulheres negras ou retenção longitudinal.

## 5. Preparação de carga — SOMENTE se banco estiver vazio e houver nova autorização

Os CSVs completos estão no repositório em `data/processed/*.csv.gz`. Os loaders existentes em `src/load.py` e `src/load_enade.py` esperam `*.csv` e aceitam `--csv`. Antes de executá-los, o Codex deve **ou** implementar e testar leitura gzip nas cargas **ou** descompactar localmente os arquivos para um diretório ignorado pelo Git sem sobrescrever arquivos existentes.

Os arquivos esperados são:
- `data/processed/censo_2024_area1.csv` (CP1252);
- `data/processed/enade_2023_area1.csv` (UTF-8).

Ordem proposta para um **banco de teste descartável**:
1. Inspecionar o schema alvo e executar o `sql/schema.sql` conforme necessidade, com transação e sem aplicar migrações cegamente.
2. Validar localmente os dois CSVs.
3. Executar `python -m src.load --csv data/processed/censo_2024_area1.csv`.
4. Executar `python -m src.load_enade --csv data/processed/enade_2023_area1.csv`.
5. Instalar a view `sql/views.sql` somente após checar dependências e privilégios.
6. Executar queries de verificação e segunda carga (idempotência) somente em ambiente descartável.
7. Propor o procedimento adaptado à Aiven real; **aguardar aprovação específica** antes de qualquer escrita.

Não imprimir `.env`, `AIVEN_TOKEN`, `DB_PASSWORD`, `service_uri` ou estados do Terraform. A autenticação PostgreSQL para carga é distinta do token da API Aiven. Use TLS, de preferência `verify-full` com CA da Aiven, em contexto local autorizado.

## 6. Terraform: cuidado com serviço preexistente

O `terraform/` declara `aiven_pg.observatorio` no plano gratuito e foi validado localmente. Não execute `terraform apply` em estado vazio apontando para um serviço que já existe: isso poderá tentar criar outro serviço. Uma **importação** pode ser apropriada após a equipe confirmar proprietário, estado Terraform existente e backup, mas requer autorização específica. Se `terraform plan` indicar criar, atualizar plano, substituir ou destruir serviço: parar e pedir revisão.

## 7. Critérios para considerar a Etapa 6C concluída

- Conta, projeto e serviço Aiven identificados; plano Free e disponibilidade comprovados.
- Auditoria SQL **real** e resultados documentados sem credenciais.
- Se o banco já estiver carregado, paridade com os valores esperados.
- Se estiver vazio, plano de carga testado localmente e execução real somente após aprovação.
- Conexão remota autenticada/TLS demonstrada sem expor segredos.
- Nenhuma operação paga ou destrutiva executada sem autorização.
- Status do dashboard online mantido explicitamente **pendente** (não substituído por PG Studio).

Este roteiro é preparatório: publicar documentos e SQL de leitura não equivale a integrar o banco remoto.
