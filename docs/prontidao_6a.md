# Relatório de prontidão para publicação

**Resultado** · versão consolidada e validada localmente. A publicação e a verificação na conta Aiven permanecem pendentes.

## Consolidação

O ponto de partida foi a cópia de trabalho após a Etapa 5B. Os 40 arquivos existentes foram comparados com os pacotes aprovados das Etapas 2, 3, 4A, 4B, 5A e 5B antes das alterações. Os pacotes anteriores serviram de referência para a comparação.

A distribuição mantém o ETL, as cargas, a modelagem SQL, as migrações, o Terraform, o dashboard, seus testes e a documentação atual. Inclui as amostras agregadas do projeto e o dicionário oficial do Censo. Foram excluídos da distribuição a nota auxiliar da auditoria, o guia geral da turma e um roteiro de apresentação provisório. Os dados completos das verificações ficam fora do pacote. A versão inclui um manifesto SHA-256 e o lockfile do provedor Terraform 4.66.0.

## Preparação técnica

| Área | Resultado |
|---|---|
| Runtime | Python 3.12.14 usado nos testes. O Community Cloud será configurado para Python 3.12. |
| Dependências | Um `requirements.txt` na raiz com versões diretas fixadas. O arquivo duplicado no diretório do aplicativo foi retirado. Instalação em ambiente virtual novo e `pip check` concluídos. |
| Arquivo principal e tema | `app/app.py`, com `.streamlit/config.toml` na raiz. O tema da Etapa 5B foi preservado. |
| Configuração e segurança | Variáveis de ambiente ou seção `[observatorio]` dos Secrets. Consulta da view em conexão de duração limitada com padrão somente leitura. Falhas mostram mensagem genérica e registram somente tipo e SQLSTATE. |
| TLS | `require` continua como padrão. O manual orienta `verify-full` com CA do projeto para publicação. A CA pode ser informada por caminho local ou como PEM nos Secrets. |
| Fontes | `auto` mantém CSV local e permite fallback identificado. `postgres` exige a view e consulta o banco sem cache nem fallback. Cache local e cache PostgreSQL em modo automático têm TTL de 120 segundos e até duas entradas cada. |
| Apresentação | Cartões, tabelas de percentuais e gráficos usam vírgula decimal. Os cálculos, filtros, identidade visual e modelo de dados foram preservados. |

## Validação executada

- **26 testes automatizados passaram**, com PostgreSQL 16.2 descartável e comparação com os CSVs completos. Foram testados inicialização sem credenciais, configuração incompleta, precedência de ambiente, leitura de Secrets, disponibilidade do fallback conforme o modo, proteção da mensagem e remoção do arquivo temporário da CA.
- **Streamlit real no Chromium.** Três processos locais novos abriram o aplicativo sem dados e sem credenciais, com os CSVs completos e no modo obrigatório PostgreSQL com Secrets locais. Os dois modos com dados exibiram 7.078 cursos, 1.269.093 matrículas, 20,2% de participação feminina, 41,2% de pretos e pardos entre declarados, 21,7% de composição de desvinculação e média ENADE 41,8.
- **TLS local.** A distribuição PostgreSQL do ambiente não tinha TLS nativo. A aplicação foi testada com `verify-full` em um proxy TLS local encaminhando para o PostgreSQL descartável. Uma CA sintética e o hostname correto permitiram a consulta. Um hostname fora do certificado foi rejeitado e a interface exibiu a mensagem genérica.
- **Infraestrutura.** `terraform fmt -check`, `terraform init -backend=false -lockfile=readonly` e `terraform validate` passaram com Terraform 1.14.7 e `aiven/aiven` 4.66.0. O teste não precisou de token.
- **Memória e abertura.** Uma sessão local por modo, medindo o tempo da navegação até o estado visível e o pico de memória residente do processo Streamlit. O PostgreSQL era local e seu processo não foi contado.

| Modo local | Tempo para abrir | Pico de memória |
|---|---:|---:|
| Sem fontes | 1,49 s | 168 MiB |
| CSVs completos | 2,97 s | 443 MiB |
| PostgreSQL | 2,82 s | 227 MiB |

O PostgreSQL entregou somente o agregado necessário ao painel. A leitura CSV processou 110.022 linhas do Censo e consumiu mais memória. As medições são uma referência local de sessão única. Capacidade simultânea, rede, hibernação, tamanho do banco remoto e limites efetivos da hospedagem precisam ser aferidos após a autorização.

## Pendências Aiven e publicação

Confirmar serviço ativo e plano, hostname e porta, banco, view publicada, permissões do usuário de leitura, CA e conectividade a partir do Community Cloud. A equipe precisa indicar o repositório e a branch aprovados, configurar os segredos no painel e conferir a fonte ativa após a publicação. Nenhuma conta real, credencial real, operação Terraform remota, publicação ou alteração em banco compartilhado foi usada para produzir esta versão. [Manual de publicação](publicacao.md)
