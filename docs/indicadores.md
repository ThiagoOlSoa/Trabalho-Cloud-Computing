# Indicadores do Observatório

O painel usa uma linha por curso. O Censo da Educação Superior 2024 contribui com as dimensões 1 e 2 e o ENADE 2023 é associado por código de curso. Na referência completa, 7.078 dos 7.085 cursos carregados entram no painel. Os sete restantes têm registros exclusivamente na dimensão 3. A barra lateral indica se a leitura veio dos CSVs ou do PostgreSQL.

## Fórmulas

As somas abaixo consideram somente os cursos selecionados pelos filtros. As fórmulas das porcentagens são razões de somas, ponderadas pelo tamanho de cada população.

| Indicador | Fórmula e fonte |
|---|---|
| Cursos no recorte e tecnológicos | Contagem de códigos de curso distintos. Para o subtítulo, a contagem se limita ao grau tecnológico informado no Censo. |
| Matrículas, ingressantes e concluintes | Somas de `QT_MAT`, `QT_ING` e `QT_CONC` do Censo 2024, respectivamente. Matrículas no Censo incluem vínculos cursando ou formados. |
| Participação feminina | `100 × Σ feminino / Σ total`, em cada população do Censo. O cartão usa as matrículas. |
| Participação preta/parda entre declaradas | `100 × Σ (preta + parda) / Σ (total − CORND)`, em cada população do Censo. O cartão usa as matrículas. `CORND` reúne informação indisponível ou não declarada. |
| Desvinculação e trancamento na composição | `100 × Σ situação / Σ (QT_MAT + trancados + desvinculados + transferidos + falecidos)`. Cada proporção usa o mesmo denominador de situações anuais. |
| Cursos com ENADE e percentual de cobertura | Cursos com correspondência no agregado ENADE 2023 e `100 × cursos com correspondência / cursos selecionados`. A presença de um curso no agregado independe de ter notas válidas. Com o filtro ENADE ativo, a cobertura é 100% se houver cursos na seleção. |
| Média geral ENADE | `Σ (MEDIA_NT_GER × QT_NOTAS_VALIDAS) / Σ QT_NOTAS_VALIDAS`. Os dois termos consideram somente cursos com correspondência, nota geral entre 0 e 100 e peso positivo. Uma nota zero é válida. |
| Raça/cor não informada | No Censo, `100 × Σ CORND / Σ matrículas`. No ENADE, `100 × Σ (não declarou + sem resposta) / Σ registros`. Contagens declaradas são a diferença entre o total da fonte e essas categorias. |

Em indicadores com denominador ausente ou igual a zero, o cartão exibe um traço, a média exibe “Sem notas válidas” e tabelas e gráficos deixam a medida vazia. Uma contagem conhecida igual a zero continua visível. Em medidas obrigatórias do Censo, uma lacuna invalida a soma correspondente. `sql/interseccionalidade.sql` usa todos os cursos da view por padrão. Para conferir uma seleção do painel, aplique os mesmos filtros à entrada da consulta.

## Comparações por curso

O painel compara composições de ingressantes, matrículas e concluintes como populações observadas em 2024. Essas diferenças não medem transições nem taxas de conclusão de uma coorte. As proporções de desvinculação e trancamento representam a composição anual de vínculos. Uma taxa longitudinal exige acompanhamento de coorte.

A matriz usa cursos com pelo menos 30 matrículas e base para calcular os dois percentuais. Agrupa por modalidade no Censo e pelas faixas de participação feminina (<10%, 10–20%, >20%) e preta/parda entre declaradas (<25%, 25–50%, >50%). Cada célula agrega cursos, matrículas, concluintes, composição de vínculos e média ENADE ponderada. O cruzamento das duas proporções marginais não fornece a contagem ou o desempenho de mulheres negras. Os resultados do ENADE descrevem o subconjunto disponível de outra edição e população, com cobertura desigual entre cursos.

## Filtro geográfico

A UF do presencial representa a UF de oferta informada pelo Censo. Cursos presenciais sem UF confiável usam “UF indisponível”. A view existente pode fornecer sua UF via ENADE em caso de divergência de modalidade, e a aplicação desconsidera essa UF para a análise do Censo. Na referência, cada curso presencial tem uma única linha de dimensão 1 e a modalidade não diverge entre as fontes.

Todos os cursos EaD usam “EaD · UF não atribuída”. No CSV anterior, a primeira UF agregada podia classificar o curso. Na leitura PostgreSQL, a UF do ENADE podia classificar o curso. A referência possui 1.059 cursos EaD com mais de uma UF na dimensão 2. Os totais somados por curso não representam a distribuição por UF nem localizam a sede da IES. Escolher uma UF do presencial exclui EaD da seleção, e escolher a categoria EaD preserva os totais nacionais desses cursos.

Para uma análise territorial EaD futura, valide a semântica e a cobertura das medidas geográficas no dicionário do INEP e proponha uma consulta separada no grão curso × dimensão × localidade. A associação de notas por curso deve continuar no grão de curso, para que apareçam uma única vez na média. Uma mudança estrutural requer aprovação.

## Verificação local

Execute `python -m unittest discover -s tests -v` com as dependências do projeto. Os testes do painel usam o AppTest do Streamlit e CSVs temporários sintéticos. Para o teste adicional de paridade integral, aponte `ETL_TEST_CSV_DIR` para os CSVs da Etapa 4A, `ETL_TEST_PG_SOCKET` para o socket Unix de um PostgreSQL descartável e `ETL_TEST_DB_NAME` para um banco local com a carga completa da Etapa 4B. O usuário é definido por `ETL_TEST_PG_USER` ou assume o padrão `agent`. A comparação usa a porta local 5432. O teste confere os indicadores, as opções de filtros, os agrupamentos e as consultas SQL selecionadas.
