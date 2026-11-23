# Dashboard do Observatório no Grafana

## Fonte PostgreSQL

Depois de o responsável confirmar o esquema e autorizar a conexão, em **Connections → Data sources → Add data source**, selecione **PostgreSQL**. Preencha no editor da fonte:

| Campo | Configuração |
|---|---|
| Host URL | Hostname e porta do serviço, sem esquema, usuário ou senha na URL |
| Database | `defaultdb` do serviço Aiven confirmado pela equipe |
| Username | Usuário dedicado, sem privilégios administrativos, com leitura limitada às colunas usadas nas seis tabelas do Observatório |
| Password | Apenas no campo protegido da fonte Grafana |
| TLS/SSL Mode | `verify-full` com a CA do serviço. No Cloud, carregue a CA pelo método de conteúdo do certificado |
| PostgreSQL version | Versão real do servidor |
| Connection limits | Comece com 3 conexões abertas, 1 ociosa e desative o ajuste automático de ociosas |

Peça ao administrador que confirme os privilégios efetivos, inclusive os herdados de `PUBLIC`. O papel precisa de `CONNECT` no banco, `USAGE` no esquema `public` e `SELECT` nas colunas listadas no [preflight](preflight_aiven.sql). O [exemplo de permissões testadas](../tests/fixtures/grafana_permissoes.sql) usa concessões por coluna. Mantenha `standard_conforming_strings=on` e defina um `statement_timeout` adequado. O role deve carecer de permissões de escrita mesmo se alguém usar a API da fonte fora dos painéis. A função Viewer no Grafana limita a edição do dashboard e ainda permite emitir consultas à fonte acessível. Se preciso, use uma instância dedicada ao projeto, com essa fonte como único acesso ao banco. Após aprovação, valide o preflight como o papel de leitura. Em seguida, selecione **Save & test** e confira as consultas fazendo login no Grafana com o perfil Viewer. [Configuração do PostgreSQL no Grafana](https://grafana.com/docs/grafana/latest/datasources/postgres/configure/) · [Segurança das fontes no Grafana](https://grafana.com/docs/grafana/latest/administration/data-source-management/#data-source-permissions) · [Usuário PostgreSQL Aiven de leitura](https://aiven.io/docs/products/postgresql/howto/readonly-user)

## Importação e uso

1. Em **Dashboards → New → Import**, envie [dashboard_observatorio.json](dashboard_observatorio.json).
2. No campo **PostgreSQL do Observatório**, selecione a fonte criada acima e clique em **Import**. O Grafana resolve a referência `DS_POSTGRESQL` na importação.
3. Abra o painel com os cinco filtros dimensionais em **All** e ENADE em **Todos**. Compare os cartões com a [referência validada](../docs/dashboard_grafana.md). Teste **Apenas com registro** e confirme cobertura de 100% se houver cursos no recorte.
4. Em **Preferences**, selecione **Português (Brasil)** para a interface. Os cartões são formatados em português pelo SQL. Os gráficos e tabelas mantêm valores numéricos e seguem a localidade do navegador para os decimais. No celular, role as tabelas horizontalmente para acessar as colunas.
5. Para editar SQL ou configuração dos painéis, modifique os arquivos-fonte e gere o JSON na raiz do repositório:

```sh
python grafana/gerar_dashboard.py
python grafana/gerar_dashboard.py --check
python -m unittest discover -s tests -p 'test_grafana.py' -v
```

Para os testes SQL em PostgreSQL descartável, siga a [reprodução do legado](../docs/dashboard_grafana.md#como-reproduzir-os-testes-locais).

## Acesso do professor

- **Grafana Cloud Free com login.** Depois de autorizar a publicação, convide o professor como **Viewer** em **Administration → Users and access** e envie o link normal do dashboard. O Viewer pode usar os filtros. A tabela de preços limita o Free a **três usuários ativos por mês**. Reserve uma vaga para o professor, considerando os acessos da equipe. [Preços e limites](https://grafana.com/pricing/) · [Papéis do Grafana](https://grafana.com/docs/grafana/latest/administration/roles-and-permissions/)
- **Link público externo.** A documentação do Grafana informa que o compartilhamento externo não suporta variáveis nem consultas que as utilizam. Os painéis deste dashboard dependem delas, então o link público não serve para a avaliação interativa. O compartilhamento externo dirigido por e-mail está em preview restrito e não é uma alternativa gratuita confirmada. [Limitações do compartilhamento externo](https://grafana.com/docs/grafana/latest/visualizations/dashboards/share-dashboards-panels/shared-dashboards/)
- **Rede.** A conexão sai do backend Grafana. No Cloud, a fonte precisa de um endpoint PostgreSQL alcançável, DNS, porta e TLS autorizados. Se houver allowlist, confirme as faixas de saída aplicáveis ao stack Grafana antes de autorizar a rede. Se o banco só aceitar rede privada, avalie Private Data Source Connect e a disponibilidade no plano com o responsável. Mantenha a rede atual até essa revisão. [Rede e fontes do Grafana Cloud](https://grafana.com/docs/grafana-cloud/connect-externally-hosted/data-sources/) · [Configuração de Private Data Source Connect](https://grafana.com/docs/grafana-cloud/connect-externally-hosted/private-data-source-connect/configure-pdc/)
- **Alternativa gratuita para apresentação ao vivo.** Se login ou rede impedirem o acesso do professor, apresente o Grafana OSS local com o PostgreSQL descartável via compartilhamento de tela. Essa opção permite demonstrar os filtros e os dados de referência. O acesso online independente continua dependente de publicação aprovada.
