# Etapa 6B — Teste do dashboard com CSV no Streamlit Community Cloud

> Roteiro histórico do ensaio CSV. Os dois gzip completos já estão versionados. Consulte o [README](../README.md) para o procedimento atual.

Este é um **piloto com dados locais versionados**, anterior à integração Aiven. Não comprova o requisito da conexão Aiven do barema.

## Dados a colocar no repositório

Coloque **exatamente estes dois arquivos** em `data/processed/`:

- `censo_2024_area1.csv.gz` (Censo 2024 processado, CP1252, `;`).
- `enade_2023_area1.csv.gz` (ENADE 2023 agregado, UTF-8, `;`).

Os arquivos são versões gzip sem perda dos CSVs de referência. O código procura primeiro `.csv` quando existe, depois `.csv.gz`. `pandas.read_csv` reconhece o gzip pelo sufixo. O `.gitignore` permite exclusivamente esses dois nomes compactados, mantendo os arquivos brutos e CSVs descompactados excluídos.

Para enviar pelo navegador no GitHub, acesse a pasta `data/processed/`, escolha **Add file → Upload files**, arraste os dois `.csv.gz` e confirme o commit. Não envie o ZIP que contém os dois, nem o original de ~90 MB. Não adicione senhas, `.env` ou dados individuais confidenciais.

## Publicar

1. Entre em [Streamlit Community Cloud](https://share.streamlit.io/) e conecte a conta GitHub que tem acesso ao repositório privado.
2. Clique em **Create app** e escolha o repositório `ThiagoOlSoa/Trabalho-Cloud-Computing`.
3. Selecione branch `main` e arquivo principal `app/app.py`.
4. Nas configurações avançadas, escolha Python **3.12**.
5. Em **Secrets**, use somente:

   ```toml
   [observatorio]
   APP_DATA_MODE = "csv"
   ```

6. Publique e aguarde a inicialização. O `requirements.txt` na raiz deve ser instalado automaticamente.

No modo CSV, não é preciso configurar `DB_HOST`, `DB_USER`, `DB_PASSWORD`, token Aiven nem certificados. Não cole credenciais do banco nesse teste.

## Checklist de aceitação

- A página exibe **Fonte ativa: CSVs Locais (data/processed/)**, não PostgreSQL.
- Sem filtros, os seis cartões indicam 7.078 cursos, 1.269.093 matrículas, participação feminina 20,2%, participação preta/parda entre declaradas 41,2%, composição de desvinculação 21,7% e ENADE 41,8.
- Cobertura ENADE: 1.665 de 7.078 cursos.
- Os filtros por grau, modalidade, rede, UF e área Cine alteram cartões e gráficos.
- Cursos EaD aparecem no agrupamento de UF `EaD · UF não atribuída`.
- As abas Panorama, Perfis dos cursos e Qualidade abrem sem erro.
- Testar uma seleção sem cursos, voltar aos filtros originais e verificar se a interface se recupera.
- Abrir em largura desktop e celular; observar memória/performance no Streamlit Cloud.

## Diagnóstico de falhas

- **Nenhuma fonte de dados**: confirme que os dois arquivos estão em `data/processed/` na branch publicada, com os nomes exatos. O CSV-resumo de indicadores não substitui esses arquivos.
- **Falha de instalação**: verifique versão do Python, `requirements.txt` e logs do Community Cloud.
- **Uso elevado de RAM**: a leitura completa de 110.022 linhas pode consumir várias centenas de MiB; usar Aiven é a solução de produção preferencial.
- **Fonte PostgreSQL em vez de CSV**: ajuste `APP_DATA_MODE = "csv"` na seção `[observatorio]` e reinicie a aplicação.

## Próximo passo após a aprovação do piloto

Confirmar o PostgreSQL Aiven com a equipe, configurar conta somente leitura e Secrets sem registrar credenciais no GitHub. Mudar para `APP_DATA_MODE = "postgres"`, retirar os CSVs compactados da implantação final se desejado e comprovar a consulta à view real. Terraform já foi validado localmente, mas ainda requer conferência no serviço existente.

Este guia documenta a preparação; a publicação real depende de ação na conta Streamlit e do upload dos dois arquivos compactados.
