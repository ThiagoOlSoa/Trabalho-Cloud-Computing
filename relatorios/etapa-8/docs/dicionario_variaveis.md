# Variáveis utilizadas no recorte

O Censo fornece vínculos agregados por curso, ano, dimensão e localização. O ENADE publicado para este projeto está agregado por curso e edição. A unidade dos dashboards é o curso. [Dicionário oficial do Censo 2024](referencia_inep/dicionario_dados_educacao_superior_2024.xlsx)

| Variáveis | Uso |
|---|---|
| `NU_ANO_CENSO`, `NU_ANO` | Edições 2024 do Censo e 2023 do ENADE |
| `CO_CURSO` | Código do curso. A consulta compara a chave inteira do Censo com o código ENADE normalizado em texto |
| `TP_DIMENSAO` | A dimensão 1 fornece oferta presencial e a 2, a agregação EaD no recorte. As linhas da dimensão 3 permanecem na base |
| `CO_IES`, `CO_CINE_ROTULO`, `ID_LOCALIZACAO` | Chaves de dimensão. O rótulo Cine vem de `NO_CINE_ROTULO` |
| `TP_GRAU_ACADEMICO`, `TP_MODALIDADE_ENSINO`, `TP_REDE` | Grau, modalidade Censo e rede. `SG_UF` é usada para oferta presencial. `CO_MODALIDADE` do ENADE ajuda a identificar divergências de modalidade |
| `QT_ING`, `QT_MAT`, `QT_CONC` | Ingressantes, matrículas e concluintes. `QT_MAT` conta vínculos em situação cursando e/ou formado |
| Sufixos `_FEM`, `_PRETA`, `_PARDA`, `_CORND` | Contagens marginais por sexo ou raça/cor para cada população. `CORND` indica raça/cor indisponível ou não declarada |
| `QT_SIT_TRANCADA`, `QT_SIT_DESVINCULADO`, `QT_SIT_TRANSFERIDO`, `QT_SIT_FALECIDO` | Contagens de situações anuais de vínculo. Com matrículas, compõem o denominador de desvinculação |
| `QT_PARTICIPANTES`, `QT_NOTAS_VALIDAS`, `MEDIA_NT_GER` | Participantes ENADE, número de notas válidas e média geral por curso |
| `QT_RACA_NAO_DECLARA`, `QT_RACA_SEM_RESPOSTA` | Informação de raça/cor indisponível no agregado ENADE |
| `possui_enade_2023` | Indicador derivado da presença da chave no agregado. Um curso pode ter registro e não ter notas válidas |

A participação feminina divide as matrículas femininas pelo total de matrículas. A participação preta/parda usa apenas matrículas com raça/cor declarada. A média ENADE pondera pelo número de notas válidas. A composição de desvinculação é anual. A matriz compara características dos cursos e os dados públicos usados no projeto fornecem totais marginais. Uma ampliação para estimar resultados de mulheres negras exigiria dados oficiais agregados conjuntamente por sexo, raça/cor e situação, com proteção contra reidentificação. Uma taxa longitudinal exigiria observações de coorte. [Fórmulas e casos sem dados](indicadores.md)
