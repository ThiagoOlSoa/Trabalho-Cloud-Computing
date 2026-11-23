# Observatório de Evasão e Retenção

Projeto acadêmico de análise de cursos da Área 1, com foco em Exatas, Engenharia, Tecnologia e Matemática. Usa os microdados oficiais do Censo da Educação Superior 2024 e o agregado do ENADE 2023 pelo código do curso, no contexto dos ODS 5 e 18.

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
