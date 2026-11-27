# Etapa 6C — Integração com Aiven PostgreSQL (sem Streamlit Cloud)

> Roteiro histórico do PG Studio. Para o banco legado, use o [preflight de colunas](../sql/preflight_painel.sql) e a [validação direta](../scripts/validar_indicadores.py). Os dashboards dispensam a view antiga.

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

O Free tem **1 GB de armazenamento**, **1 GB RAM**, **1 CPU**, **até 20 conexões** e restrições de serviços por organização. Não ativar plano pago, Aiven Runtime para contornar limitações.

## 3. Cenário A: serviço existente

Há registros de uso anterior no projeto. O estado atual do serviço, o esquema e a versão dos dados devem ser confirmados com o responsável. Após autorização para leitura:

1. Selecione o serviço e o banco corretos no Console. Registre estado, plano, uso do armazenamento e existência de backup recuperável.
2. Com `psql` de um usuário somente leitura, execute `psql -X -v ON_ERROR_STOP=1 -f sql/aiven_preflight.sql` no banco alvo. O script funciona em banco vazio. Mostra tamanho, objetos, permissões efetivas do usuário conectado, índices válidos, constraints e definição da view. As linhas do catálogo são estimativas. Os resultados podem incluir nomes internos.
3. Confirme a unicidade do município e do grão do Censo, a chave ENADE em `(nu_ano, co_curso)`, a FK para `dim_curso` e a existência da localização “SEM MUNICÍPIO”. Compare as definições com o repositório. Obtenha o histórico das migrações com o responsável. Um índice ou constraint presente não comprova por si só que um script específico foi executado.
4. Se as tabelas estiverem completas e legíveis, use `sql/auditoria_carga.sql` para investigar duplicatas e colisões. Se a view e as três tabelas necessárias estiverem disponíveis, execute `sql/aiven_validacao_dados.sql`. As contagens das tabelas são integrais. Se o banco guardar outras edições, separe o recorte da comparação antes de interpretar uma diferença.
5. Se esquema e indicadores estiverem de acordo, preserve o banco e use as consultas da seção de demonstração. Se houver lacunas ou divergências, registre o diagnóstico com o responsável. Compare esquema e conteúdo em uma cópia descartável com backup recuperável. Prepare um ajuste específico para revisão. Um upsert dos loaders pode atualizar chaves existentes e conserva chaves ausentes do CSV.

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

## 5. Inicialização e carga em banco confirmado vazio

Este procedimento reproduz o ensaio local. A execução remota exige aprovação específica e confirmação de que nenhum esquema ou dado do projeto precisa ser preservado. As migrações 001–003 são ajustes para esquemas legados. Um banco novo usa `schema.sql` diretamente.

Configure `PGHOST`, `PGPORT`, `PGDATABASE` e `PGUSER` para o `psql` e os campos `DB_HOST`, `DB_PORT`, `DB_NAME` e `DB_USER` para os loaders, apontando para o mesmo banco. Use o mecanismo de segredos aprovado pelo responsável. A carga usa `DB_PASSWORD`, distinto do token da API Aiven. Para conexão remota, use `PGSSLMODE=verify-full`, `DB_SSLMODE=verify-full` e `PGSSLROOTCERT` com a CA do projeto. Verifique o hostname usado pelo certificado. Use uma conta autorizada a escrever para a carga e separe-a da conta de leitura do diagnóstico.

```sh
PGOPTIONS='-c search_path=public' psql -X -v ON_ERROR_STOP=1 -1 -f sql/schema.sql
python -m src.load --csv data/processed/censo_2024_area1.csv.gz
python -m src.load_enade --csv data/processed/enade_2023_area1.csv.gz
psql -X -v ON_ERROR_STOP=1 -1 -f sql/views.sql
psql -X -v ON_ERROR_STOP=1 -f sql/aiven_validacao_dados.sql
```

Os loaders também aceitam os CSVs convencionais. Seus caminhos padrão continuam apontando para `.csv`. Use `--csv` para informar explicitamente o gzip. Cada carga valida o arquivo completo antes de se conectar. O Censo precede o ENADE pela chave estrangeira. Cada loader usa uma transação própria. Se a carga ENADE falhar, a transação do Censo já confirmada permanece no banco. Revise os resultados entre as cargas e após instalar a view.

## 6. Cenário B: serviço inexistente ou adoção pelo Terraform

Se a equipe confirmar que não há serviço a preservar, confirme também que existe um projeto Aiven e que a organização está elegível para criar o PostgreSQL gratuito. O Terraform declara um único `aiven_pg.observatorio` no plano `free-1-1gb`, deixa região e nuvem a cargo da Aiven e usa `prevent_destroy`. O lockfile fixa o provedor 4.66.0, validado anteriormente. O futuro plano deve mostrar só uma criação nesse plano gratuito e nenhuma exclusão ou substituição. O provisionamento depende de aprovação específica. [Plano PostgreSQL gratuito](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier) · [Procedimento Terraform](../terraform/README.md)

Para um serviço existente que a equipe queira colocar sob gerenciamento do Terraform, confirme titularidade, plano, backup e eventual estado que já gerencie o recurso. Uma futura importação usa o endereço `aiven_pg.observatorio` e o identificador `PROJETO/SERVICO`. Ela associa o serviço ao estado. Depois da importação autorizada, revise o plano antes de considerar qualquer alteração. Se o plano propuser criação, mudanças inesperadas de plano ou região, substituição ou exclusão, interrompa a operação. O estado e `AIVEN_TOKEN` ficam fora do repositório. [Importação de recursos Aiven](https://registry.terraform.io/providers/aiven/aiven/latest/docs/guides/importing-resources)

## 7. Roteiro de demonstração no PG Studio

O PG Studio normalmente usa `avnadmin`, com permissões de escrita. A demonstração deve usar somente os SELECTs previamente revisados. Para auditoria com menor privilégio, prefira `psql` com usuário de leitura. Confirme com o operador autorizado a permissão na Console e o acesso pela rede permitida. [Segurança do PG Studio](https://aiven.io/docs/products/postgresql/howto/pg-studio/security-connections) · [Executar consultas](https://aiven.io/docs/products/postgresql/howto/pg-studio/write-run-queries)

| Tempo | Demonstração |
| --- | --- |
| 0–2 min | Mostrar na Console o serviço PostgreSQL, plano gratuito, estado e uso de armazenamento. |
| 2–4 min | Em **Tables**, abrir o mapa de esquema e mostrar dimensões, fatos e view. Em **SQL editor**, mostrar as consultas de inventário e índices do preflight. |
| 4–7 min | Executar o SELECT de indicadores de `sql/aiven_validacao_dados.sql` e as contagens. Explicar os sete cursos da dimensão 3 preservados no Censo e fora da view. |
| 7–9 min | Executar a consulta por grau de `sql/queries.sql` ou a comparação de perfis de `sql/interseccionalidade.sql`. Explicar cobertura do ENADE e a diferença entre composição anual e trajetória longitudinal. |
| 9–10 min | Mostrar o recurso do Terraform e as proteções e encerrar com as limitações do recorte. |

Selecione cada SELECT por inteiro no editor e execute-o isoladamente se a interface tratar instruções em sessões separadas. O bloco `BEGIN ... COMMIT` é apropriado no `psql`. Compartilhe somente saídas agregadas sem nomes internos ou credenciais. A demonstração cobre infraestrutura e análise SQL. O requisito acadêmico de dashboard online com filtros segue pendente.

## 8. Estado da validação e autorizações

O ensaio com PostgreSQL 16.2 descartável passou com os dois gzip completos de `main`. O preflight funcionou antes da criação das tabelas e após o carregamento. A primeira execução e a reexecução produziram os mesmos resultados da seção 4. A auditoria não retornou grupos duplicados. O banco local ocupava cerca de 67 MiB após duas cargas, incluindo o catálogo. O valor serve de referência; o serviço real pode ter outros dados, retenção de WAL e espaço ocupado diferente.

A suíte teve 31 testes aprovados, incluindo rollback, paridade entre gzip e CSV, duplicatas normalizadas e rejeição de gzip corrompido antes da abertura da conexão. A comparação da média ponderada em ponto flutuante admite uma diferença absoluta de até `1e-12` entre as fontes; a fórmula permaneceu igual. A conexão à conta Aiven, o diagnóstico remoto, a carga, o provisionamento e a adoção pelo Terraform dependem de autorização e do responsável pela conta. O código desta etapa não modifica a interface Streamlit.
