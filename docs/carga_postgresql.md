# Validação e carga no PostgreSQL

## Banco local vazio

Em um PostgreSQL descartável, execute `sql/schema.sql` e `sql/views.sql` via `psql -X -v ON_ERROR_STOP=1`. O esquema cria as dimensões, a localização reservada, as tabelas fato e as chaves e índices exigidos pelos *upserts*. A view pode ser instalada antes da carga. Execute o Censo antes do ENADE, pois a fato ENADE depende de `dim_curso`.

Com as variáveis `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` e `DB_SSLMODE` apontando para o ambiente de teste, use:

```sh
python -m src.load --csv data/processed/censo_2024_area1.csv.gz
python -m src.load_enade --csv data/processed/enade_2023_area1.csv.gz
```

Sem `--csv`, os caminhos padrão são os CSVs em `data/processed/`. Cada comando valida o arquivo inteiro, com tipos e chaves canônicos, e grava em uma única transação. A carga do Censo atualiza dimensões e fatos pelas chaves existentes e rejeita atributos divergentes para uma mesma chave dentro do arquivo. A carga do ENADE confirma que todos os cursos constam em `dim_curso` antes de gravar. Cargas sucessivas atualizam as mesmas chaves e preservam registros ausentes do CSV. Os dois comandos têm transações separadas. Erros do driver são reportados por classe e SQLSTATE. Se a conexão cair durante a confirmação, confira o estado da carga no banco antes de concluir o diagnóstico.

## Banco com histórico

Antes de escolher as migrações, inspecione o DDL instalado, índices, chaves, dependências, permissões da view e dados. Use uma cópia descartável e o backup autorizado do esquema e dos dados. Essas migrações descrevem a evolução de versões conhecidas do projeto.

1. Execute `sql/auditoria_carga.sql` em modo somente leitura. As consultas listam chaves e IDs com duplicação, colisões que uma consolidação de municípios poderia produzir, número de variantes e colisões após normalizar a chave ENADE. Para avaliar os grupos, compare os registros originais por esses IDs e documente qual origem tem precedência. Uma única variante indica conteúdo igual nos campos comparados. Duas ou mais exigem revisão. Qualquer saneamento deve ser planejado e aprovado separadamente.
2. A **001** verifica a chave ENADE. Mantém a chave composta se já existir, migra a chave legada por curso e interrompe diante de chave primária inesperada ou chaves nulas ou duplicadas.
3. A **002** exige uma localização reservada e interrompe ao detectar duplicatas de municípios ou fatos. Se o esquema estiver íntegro, cria os índices únicos e confirma que o PostgreSQL consegue usá-los nas cláusulas de conflito. Não há exclusão ou remapeamento de registros.
4. A **003** verifica chaves ENADE inválidas, colisões de normalização e cursos sem correspondente. Quando o tipo de curso é textual, remove a view com `RESTRICT`, converte a coluna e recria a view antes do `COMMIT`. Se a view tiver permissões explícitas, comentários, opções ou outro proprietário, ou se o usuário tiver privilégios padrão próprios aplicáveis, prepare uma migração específica para preservar esses metadados. Dependências de outros objetos também podem impedir a remoção. Se o tipo já for inteiro, usa a substituição da view existente. Uma falha mantém a definição anterior por rollback. Execute o arquivo com `psql`, pois a leitura de `views.sql` usa `\ir`.

Os CSVs de referência registram 7.085 cursos do Censo. A view mantém as dimensões 1 e 2 e expõe 7.078 cursos. Os sete cursos exclusivamente na dimensão 3 permanecem na fato e na dimensão de cursos. A integração usa curso e os anos definidos na view. Os códigos de IES das duas fontes mantêm seus significados originais.

## Testes

Execute `python -m unittest discover -s tests -v`. Para incluir os testes reais, configure `ETL_TEST_PG_SOCKET` com o diretório do socket Unix de um servidor PostgreSQL exclusivamente descartável, `ETL_TEST_PG_USER` com o usuário local autorizado a criar bancos e, se necessário, `ETL_TEST_PSQL` com o caminho de `psql`. Os testes criam e removem apenas bancos temporários com nomes próprios e registros sintéticos.
