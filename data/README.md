# Dados e pipeline local

O pipeline lê CSVs locais ou membros de um ZIP local, um registro por vez. A transformação seleciona apenas as colunas usadas na carga. A memória adicional cresce com a quantidade de chaves distintas, usada para detectar duplicatas e selecionar os cursos do ENADE. Cada saída é publicada após a validação completa. Escolha uma pasta de saída nova. O destino precisa permitir links físicos no mesmo sistema de arquivos para a publicação atômica.

## Executar

Na raiz do projeto, com Python 3.10 ou posterior, substitua os caminhos de exemplo pelos arquivos locais.

```sh
python -m src.transform censo --entrada data/raw/cadastro_cursos_2024.csv --saida data/validacao/censo_2024_area1.csv
python -m src.transform enade --entrada caminho/enade_agregado_2023.csv --censo-processado data/validacao/censo_2024_area1.csv --saida data/validacao/enade_2023_area1.csv
```

O Censo espera `cp1252` por padrão e o ENADE agregado espera UTF-8, com ou sem BOM. O separador padrão é `;`. Use `--encoding` e `--separador` para ajustar a leitura conforme o arquivo recebido. Se a entrada for um ZIP, use `--membro` com o caminho exato do CSV dentro dele. Use `--limite N` para ler os primeiros N registros **antes** dos filtros. Um teste com ENADE amostrado precisa de cursos em comum com o Censo de referência. As saídas são CSVs com `;`, Censo em `cp1252` e ENADE em UTF-8. Os nomes e formatos correspondem aos esperados em `data/processed/` pelas cargas existentes. Os exemplos gravam em `data/validacao/` para preservar os arquivos em uso.

Para copiar ou inspecionar um CSV como UTF-8 de forma independente, use `python -m src.extract --entrada CAMINHO --saida AMOSTRA.csv --encoding cp1252 --limite 120`. Essa etapa é opcional. Se usar o resultado da extração como entrada do Censo, informe `--encoding utf-8` à transformação.

## Censo da Educação Superior 2024

- **Origem e campos.** Use o cadastro de cursos com o cabeçalho oficial. São preservadas as 67 colunas do CSV de referência, incluindo ano, curso, IES, rede, organização, categoria, curso e grau acadêmico, modalidade, nível, dimensão, localização e códigos e rótulos Cine. A lista exata está em `CENSO_COLUMNS` no módulo `src/transform.py`. A planilha oficial consta em `docs/referencia_inep/`, aba `cadastro_cursos`.
- **Recorte.** Mantém `NU_ANO_CENSO=2024`, nível `1` (graduação) e áreas gerais Cine `05` (Ciências naturais, matemática e estatística), `06` (Computação e TIC) e `07` (Engenharia, produção e construção). A regra de nível segue o recorte observado no arquivo completo, que contém apenas graduação. O CSV histórico contém bacharelados e tecnológicos. Como a documentação da equipe não identifica filtro adicional de grau, a implementação preserva todos os graus encontrados dentro do recorte. Registros sem classificação de área ficam fora. Preserva as quatro dimensões geográficas presentes na entrada e não soma suas linhas.
- **Chave.** Ano, curso, dimensão e município. Município indisponível permanece vazio e integra a verificação de unicidade. A carga converte esse vazio para a localização reservada “SEM MUNICÍPIO”.
- **Medidas.** `QT_ING`, `QT_MAT` e `QT_CONC`, seus totais marginais por sexo e raça/cor, seis contagens por turno e contagens de trancados, desvinculados, transferidos e falecidos. Para cada total, as somas por sexo e por raça/cor precisam reconciliar separadamente. `CORND` segue a categoria do Censo para informação indisponível ou não declarada.
- **Normalização.** Chaves numéricas são convertidas para inteiros e códigos Cine mantêm sua largura. Aspas adicionais do rótulo Cine são retiradas. Geografia indisponível e grau não aplicável permanecem vazios. O marcador oficial `.` de turno não aplicável em EaD é convertido em zero para preservar o contrato da carga. Lacunas nas demais contagens obrigatórias, valores negativos, números fracionários e chaves duplicadas abortam a publicação.

## ENADE 2023

- **Entrada.** Agregado com 22 colunas no esquema de `ENADE_COLUMNS`, descrito em `docs/Dicionario.docx`. Contém ano, curso, IES do ENADE, grupo, modalidade, UF, município, região, número de registros, notas válidas, médias geral, de formação geral e do componente específico, duas contagens de sexo e sete de raça/cor.
- **Recorte e chave.** Mantém uma linha por `(NU_ANO, CO_CURSO)` da edição de 2023, restrita aos cursos presentes no Censo 2024 transformado. A IES de cada fonte é mantida em seu próprio arquivo. O campo `CO_CURSO` é a chave de correspondência.
- **Validação.** As duas contagens de sexo e as sete de raça/cor reconciliam separadamente com `QT_PARTICIPANTES`. Não declaração e ausência de resposta são categorias distintas. A quantidade de notas válidas não pode exceder os registros. As médias são decimais entre 0 e 100, inclusive. O contrato histórico documenta os mesmos totais de notas válidas nas três medidas. As médias ficam vazias quando esse total é zero. Uma nota zero é válida.
- **Limitação de origem.** O pacote disponibiliza o CSV agregado e o dicionário da equipe. Para reconstruir o agregado, faltam os arquivos de origem do ENADE 2023, o dicionário oficial da edição e a confirmação das regras de seleção e dos códigos aplicados a cada arquivo. O dicionário da equipe descreve agregações separadas de notas, sexo e raça/cor por curso e sua combinação nesse mesmo grão. O pipeline atual valida e prepara esse agregado existente.

## Interpretação e testes

As proporções por sexo e raça/cor descrevem a composição de cada população disponível. Os totais marginais não identificam a interseção de sexo e raça/cor por pessoa. Desvinculação e trancamento são contagens anuais de situações de vínculo. Uma taxa longitudinal exige acompanhamento de coorte. Censo 2024 e ENADE 2023 representam anos e populações distintos. No ENADE, `QT_PARTICIPANTES` conta registros da origem descrita pela equipe.

Execute `python -m unittest discover -s tests -v` com as dependências do projeto instaladas. Os testes usam dados sintéticos e arquivos temporários. Eles conferem o formato dos CSVs contra o contrato das cargas sem conectá-las ao PostgreSQL.
