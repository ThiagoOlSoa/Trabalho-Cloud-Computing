# Observatório de Evasão e Retenção · Entrega final

A candidata final está na branch `etapa-9-entrega-final-streamlit`, commit `9eb84b0`. A base da equipe é `a32f4e9` e o bundle preserva a Etapa 8 em `98dc179` e todo o histórico anterior. O Streamlit é a plataforma de visualização. A aplicação usa Python 3.12, consulta as seis tabelas PostgreSQL diretamente e conserva os cursos sem ENADE. Em produção, a conexão é PostgreSQL com TLS `verify-full`.

Os dois CSVs gzip completos foram validados no PostgreSQL descartável. O bundle foi aberto em clone limpo e o manifesto do checkout corresponde aos 64 arquivos listados. A conexão real a partir do Streamlit Community Cloud e o workflow hospedado da branch final aguardam publicação e homologação.

| Indicador | Resultado no recorte integral |
|---|---:|
| Cursos | 7.078 |
| Matrículas | 1.269.093 |
| Ingressantes | 673.375 |
| Concluintes | 153.760 |
| Participação feminina | 20,2% |
| Participação preta/parda entre declaradas | 41,2% |
| Composição anual de desvinculação | 21,7% |
| Cursos com ENADE | 1.665 |
| Cobertura ENADE | 23,5% |
| Média geral ENADE ponderada | 41,8 |

[Abrir a auditoria](AUDITORIA_FINAL.md) · [Ver os testes](VALIDACAO_FINAL.txt) · [Aplicar o bundle e abrir o PR](COMO_PUBLICAR.md) · [Checklist operacional](CHECKLIST_MANUAL.md)
