# Apresentação técnica do Observatório

## Roteiro de 10 minutos

Antes da apresentação, abra três abas com as evidências autorizadas: Console Aiven ou PG Studio, repositório GitHub e Grafana. Comece com todos os filtros do painel abertos. Confira com o responsável se o acesso Viewer e a ligação Grafana → Aiven foram homologados. Use o plano alternativo para o que estiver pendente.

| Tempo | Fala e demonstração | Critério atendido |
|---|---|---|
| 0:00–0:50 | Apresente a pergunta. Como gênero e raça/cor aparecem na participação acadêmica nos cursos da Área 1? Relacione a pergunta ao ODS 5 e ao ODS 18. Explique que o recorte da equipe cobre Exatas, Engenharias e Tecnologia. | ODS 5 e 18 |
| 0:50–2:00 | Mostre Censo Superior 2024 e ENADE 2023, ambos do INEP. Abra os scripts `src/extract.py` e `src/transform.py` e mostre os CSVs processados. Explique validação dos dados, carga Censo antes de ENADE, transação por carga e reexecução idempotente. | ETL e SQL |
| 2:00–3:10 | Mostre o serviço PostgreSQL Free na Aiven. Use um diagrama simples de fatos e dimensões para explicar as chaves e a agregação por curso. O Censo é agregado no recorte das dimensões 1 e 2 antes do `LEFT JOIN` com o ENADE, que usa código normalizado. | Aiven e modelagem |
| 3:10–4:10 | Abra `terraform/main.tf`. Mostre o recurso, o plano `free-1-1gb` e `prevent_destroy`. Mostre a evidência de `fmt`, `init -backend=false` e `validate`. Se o serviço já existia antes do Terraform, explique essa diferença de histórico. | IaC |
| 4:10–5:40 | Reserve este bloco para dados reais. No PG Studio, rode a validação de leitura previamente autorizada e destaque 110.022 linhas Censo, 1.665 ENADE, 7.085 cursos na dimensão e 7.078 no recorte. Explique que sete cursos têm registros apenas na dimensão 3. | Aiven e consistência dos dados |
| 5:40–7:40 | Mostre o Grafana e os cartões. Aponte grau, modalidade, rede, UF, Cine e ENADE. Faça uma seleção de modalidade ou grau. Ative **Apenas com registro** para mostrar a cobertura de 100% no subconjunto correspondente. Limpe os filtros e mostre **EaD · UF não atribuída**. Declare a origem do banco demonstrado. | Dashboard interativo |
| 7:40–9:05 | Compare 20,2% de participação feminina e 41,2% de participação preta/parda entre matrículas com raça/cor declarada. Explique os denominadores. Comente a composição anual de desvinculação de 21,7%, a cobertura ENADE de 23,5% e a média 41,8 ponderada pelas notas válidas. | Análise ODS e interpretação |
| 9:05–10:00 | Explique as limitações e conclua. Censo e ENADE são de anos e populações distintos. Retenção longitudinal exige coortes. O cruzamento individual de mulheres negras exige dados conjuntos. Indique o PR, a documentação e o status real da integração. | Documentação e apresentação |

Na falha do **Grafana**, preserve o bloco do PG Studio e use as capturas do Grafana OSS local. Se possível, abra o Grafana OSS local com PostgreSQL descartável para demonstrar os filtros. Na falha da **Aiven**, rode o verificador em PostgreSQL local com os CSVs publicados. Mostre somente evidências anteriores da Aiven cuja origem a equipe possa confirmar. Se os dois serviços estiverem indisponíveis, use a tabela de referências, o SQL, as capturas locais e a saída de testes, identificando cada fonte. Uma gravação ou captura demonstra o ensaio correspondente. O requisito de acesso online depende da homologação do ambiente de publicação.

## Checklist de evidências para o professor

| Critério e pontos | Evidência a separar | Estado ou origem |
|---|---|---|
| Serviços Aiven · 3,0 | Tela do Console com serviço PostgreSQL, plano, estado e uso. Saída dos SELECTs do PG Studio com totais e uma consulta analítica. Confirmação da fonte do Grafana quando homologada. | Indicadores reais conferidos pela equipe. Capturas do Console/PG Studio e evidência da fonte real ainda devem ser coletadas pelo responsável. |
| ETL e SQL · 2,5 | Scripts de extração e transformação, ambos os CSVs processados, execução das cargas, verificador de indicadores, reexecução sem duplicatas e evidência de rollback. | Código e dados no GitHub. Testes sobre PostgreSQL local descartável. |
| Terraform · 2,0 | `main.tf`, versão do provedor, saída de `fmt -check`, `init -backend=false` e `validate`. Identifique se o serviço já existia. | Validação reportada na Etapa 3 com Terraform 1.14.7 e Aiven 4.66.0. Reúna os logs preservados ou repita apenas a validação local autorizada. |
| ODS 5 e 18 · 1,5 | Demonstração dos seis filtros, denominadores, períodos e comparação de perfis agregados. | [Capturas de Grafana OSS local da Etapa 7A](dashboard_grafana.md#validação-visual-da-etapa-7a). A publicação e o login do avaliador ainda dependem de homologação. |
| Documentação · 0,5 | README, arquitetura, fórmulas, manual de conexão, diagrama de fatos e dimensões, branches e PRs. | [Guias do Grafana](dashboard_grafana.md) · [PR #1](https://github.com/ThiagoOlSoa/Trabalho-Cloud-Computing/pull/1) · [PR #2](https://github.com/ThiagoOlSoa/Trabalho-Cloud-Computing/pull/2) |
| Apresentação funcional · 0,5 | Roteiro de 10 minutos ensaiado, conexão autorizada ou gravação/capturas identificadas, teste de login Viewer e plano alternativo. | Preparação da Etapa 7D. Ensaiar com o ambiente que estiver aprovado no dia. |

Antes de compartilhar imagens, oculte senha, token, URI com credenciais e endereços internos. Anote **origem**, **data**, **versão ou commit** e **filtros ativos** de cada evidência. A arquitetura para o slide pode ser mostrada como `INEP → ETL Python → PostgreSQL Aiven → Grafana`, com Terraform declarando a infraestrutura e GitHub versionando a solução.
