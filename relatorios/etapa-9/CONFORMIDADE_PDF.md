# Conformidade da entrega acadêmica

Avaliação baseada no **Guia de Orientação do Projeto Prático**, seções 3 a 5. Os estados abaixo distinguem evidências coletadas em ambiente local, informações fornecidas pela equipe e operações que ainda precisam ser realizadas. A pontuação é a do barema. A atribuição da nota cabe ao professor.

| Critério | Barema | Estado | Evidência e pendência |
|---|---:|---|---|
| Arquitetura e integração Aiven Free | 3,0 | Implementado, aguardando validação real | A equipe confirmou o banco ativo, os dados e os totais no Aiven. O painel foi validado sobre um PostgreSQL descartável com o legado simulado. Falta homologar a conexão da hospedagem ao Aiven, TLS e permissões efetivas. |
| ETL e modelagem SQL | 2,5 | Atendido e comprovado | Leitura CSV e gzip, cargas transacionais, reexecução, rollback, integridade referencial e indicadores conferidos localmente com os arquivos completos. A reconstrução do ENADE a partir de microdados brutos continua fora do fluxo reproduzido. |
| Infraestrutura como código | 2,0 | Implementado, aguardando validação real | Terraform 1.14.7 e provedor Aiven 4.66.0. `fmt -check`, `init -backend=false` e `validate` passaram localmente. A equipe precisa mostrar a evidência do serviço e esclarecer seu histórico de provisionamento. |
| Relevância analítica, ODS 5 e 18 | 1,5 | Parcial | As métricas de participação, declaração de raça/cor e os perfis agregados dos cursos atendem à análise descritiva. Os dados usados não trazem desfechos individuais cruzados por sexo e raça/cor. A matriz não permite estimar evasão de mulheres negras. |
| Documentação e diagrama | 0,5 | Atendido e comprovado | README, diagrama, dicionário atual, procedimentos, manifesto reproduzível e registros históricos identificados. |
| Apresentação e demonstração | 0,5 | Parcial | Roteiro de dez minutos, checklist e alternativa local disponíveis. A demonstração ao vivo com a fonte real e o acesso do professor ainda dependem de homologação. |

O requisito obrigatório de **dashboard funcional online** está **pendente**. A apresentação usa o Streamlit. O Streamlit local com gzip ou PostgreSQL descartável serve para ensaio. Uma captura local comprova o funcionamento naquele ambiente. [Roteiro e checklist](APRESENTACAO_10_MIN.md)

## Pendências da equipe

1. No Aiven, confirmar os tipos das colunas com o preflight e revisar as permissões efetivas de um usuário com acesso de leitura às 42 colunas necessárias. Confirmar a CA, a rede e a configuração `verify-full`.
2. Configurar o Streamlit Community Cloud com `APP_DATA_MODE=postgres` e TLS `verify-full`. Comparar os dez indicadores, testar os seis filtros e verificar a fonte efetiva. [Manual Streamlit](MANUAL_AIVEN_STREAMLIT.md)
3. Publicar o dashboard aprovado, verificar a configuração pública em uma janela anônima e enviar o endereço ao professor.
4. Ensaiar o roteiro e separar evidência local de `fmt`, `init` e `validate`, evidência do serviço Free existente e resultados de leitura na Aiven. Confirmar o histórico de provisionamento antes de apresentá-lo como execução via Terraform.

Os caminhos de código neste documento referem-se ao checkout obtido com o bundle. [Aplicação do bundle](COMO_PUBLICAR.md)
