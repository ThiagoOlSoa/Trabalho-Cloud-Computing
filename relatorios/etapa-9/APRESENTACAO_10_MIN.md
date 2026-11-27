# Apresentação técnica do Observatório

## Roteiro de 10 minutos

Use o Streamlit para a demonstração. Abra o Streamlit Community Cloud, o Console Aiven ou PG Studio e o repositório da equipe. Comece com todos os filtros abertos. Confirme que a origem é **PostgreSQL remoto**, o TLS está ativo e que o link público funciona em janela anônima. Se a homologação estiver pendente, siga o plano de contingência.

| Tempo | Fala e demonstração | Critério atendido |
|---|---|---|
| 0:00–0:50 | Apresente a pergunta. Como gênero e raça/cor aparecem na participação acadêmica nos cursos da Área 1? Relacione a pergunta ao ODS 5 e ao ODS 18. Explique que o recorte da equipe cobre Exatas, Engenharias e Tecnologia. | ODS 5 e 18 |
| 0:50–2:00 | Mostre Censo Superior 2024 e ENADE 2023, ambos do INEP. Abra os scripts `src/extract.py` e `src/transform.py` e mostre os CSVs processados. Explique validação dos dados, carga Censo antes de ENADE, transação por carga e reexecução idempotente. | ETL e SQL |
| 2:00–3:10 | Mostre o serviço PostgreSQL Free na Aiven. Use um diagrama simples de fatos e dimensões para explicar as chaves e a agregação por curso. O Censo é agregado no recorte das dimensões 1 e 2 antes do `LEFT JOIN` com o ENADE, que usa código normalizado. | Aiven e modelagem |
| 3:10–4:10 | Abra `terraform/main.tf`. Mostre o recurso, o plano `free-1-1gb` e `prevent_destroy`. Mostre a evidência de `fmt`, `init -backend=false` e `validate`. Se o serviço já existia antes do Terraform, explique essa diferença de histórico. | IaC |
| 4:10–5:40 | Reserve este bloco para dados reais. No PG Studio, rode as contagens de leitura previamente autorizadas e destaque 110.022 linhas Censo, 1.665 ENADE, 7.085 cursos na dimensão e 7.078 no recorte. Explique que sete cursos têm registros apenas na dimensão 3. | Aiven e consistência dos dados |
| 5:40–7:40 | Mostre o Streamlit e os cartões. Aponte grau, modalidade, rede, UF, Cine e ENADE. Faça uma seleção de modalidade ou grau. Ative **Somente cursos com ENADE 2023** para mostrar a cobertura de 100% no subconjunto correspondente. Limpe os filtros e mostre **EaD · UF não atribuída**. Declare a origem do banco demonstrado. | Dashboard interativo |
| 7:40–9:05 | Compare 20,2% de participação feminina e 41,2% de participação preta/parda entre matrículas com raça/cor declarada. Explique os denominadores. Comente a composição anual de desvinculação de 21,7%, a cobertura ENADE de 23,5% e a média 41,8 ponderada pelas notas válidas. | Análise ODS e interpretação |
| 9:05–10:00 | Explique as limitações e conclua. Censo e ENADE são de anos e populações distintos. Retenção longitudinal exige coortes. O cruzamento individual de mulheres negras exige dados conjuntos. Indique o PR, a documentação e o status real da integração. | Documentação e apresentação |

Se o Streamlit Community Cloud estiver indisponível, apresente as consultas previamente autorizadas no PG Studio e abra o Streamlit local. Se a Aiven estiver indisponível, inicie o Streamlit local com `APP_DATA_MODE=csv`, mostre a origem visível e demonstre os mesmos filtros com os gzip completos. Preserve a identificação de origem de capturas e registros de testes. O requisito de acesso online depende da homologação da publicação em modo PostgreSQL.

## Checklist de evidências para o professor

| Critério e pontos | Evidência a separar | Estado ou origem |
|---|---|---|
| Serviços Aiven · 3,0 | Tela do Console com serviço PostgreSQL, plano, estado e uso. Saída dos SELECTs do PG Studio com totais e uma consulta analítica. Confirmação da fonte do Streamlit quando homologada. | Indicadores reais conferidos pela equipe. Capturas do Console/PG Studio e evidência da fonte real ainda devem ser coletadas pelo responsável. |
| ETL e SQL · 2,5 | Scripts de extração e transformação, ambos os CSVs processados, execução das cargas, verificador de indicadores, reexecução sem duplicatas e evidência de rollback. | Código e dados no GitHub. Testes sobre PostgreSQL descartável. A consulta compartilhada é usada pelo Streamlit e pelo verificador. |
| Terraform · 2,0 | `main.tf`, versão do provedor, saída de `fmt -check`, `init -backend=false` e `validate`. Identifique se o serviço já existia. | Validação reportada na Etapa 3 com Terraform 1.14.7 e Aiven 4.66.0. Reúna os logs preservados ou repita apenas a validação local autorizada. |
| ODS 5 e 18 · 1,5 | Demonstração dos seis filtros, denominadores, períodos e comparação de perfis agregados. | Streamlit validado localmente. A publicação e o teste do link pelo avaliador aguardam homologação. |
| Documentação · 0,5 | README, arquitetura, fórmulas, manual de conexão, diagrama de fatos e dimensões, branches e PRs. | [Arquitetura](arquitetura.md) · [Dicionário](dicionario_variaveis.md) · [Manual](MANUAL_AIVEN_STREAMLIT.md) |
| Apresentação funcional · 0,5 | Roteiro de 10 minutos ensaiado, conexão autorizada ou gravação/capturas identificadas, teste do link público e plano alternativo. | Preparação da Etapa 7D. Ensaiar com o ambiente que estiver aprovado no dia. |

Antes de compartilhar imagens, oculte senha, token, URI com credenciais e endereços internos. Anote **origem**, **data**, **versão ou commit** e **filtros ativos** de cada evidência. A arquitetura para o slide pode ser mostrada como `INEP → ETL Python → PostgreSQL Aiven → Streamlit Community Cloud`, com Terraform declarando a infraestrutura e GitHub versionando a solução.

Os caminhos de código neste documento referem-se ao checkout obtido com o bundle. [Aplicação do bundle](COMO_PUBLICAR.md)
