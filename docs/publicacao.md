# Manual de publicação no Streamlit Community Cloud

Use este manual após a aprovação da publicação. O Community Cloud precisa de acesso a um repositório GitHub com o projeto. O painel pode consultar diretamente a view PostgreSQL com um usuário de leitura. O ambiente de publicação usa a raiz do repositório para localizar o tema e pode dar prioridade ao manifesto ao lado do arquivo principal. Este projeto usa um único `requirements.txt` na raiz. [Organização dos arquivos](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization) · [Dependências](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)

## Preparar e validar em um computador

1. Extraia o ZIP em uma pasta nova. Compare os hashes com `MANIFESTO_SHA256.txt`. Em Linux, a partir da raiz, use `sha256sum -c MANIFESTO_SHA256.txt`.
2. Crie um ambiente virtual Python 3.12 e ative-o. Instale com `python -m pip install -r requirements.txt` e confira com `python -m pip check`.
3. Execute `python -m streamlit run app/app.py` na raiz para aplicar `.streamlit/config.toml`. Sem fontes configuradas, o painel deve explicar que precisa dos CSVs ou do PostgreSQL. Para modo local sem banco, forneça os dois CSVs processados em `data/processed/`. [Preparação dos dados](../data/README.md)
4. Prepare o repositório e a branch aprovados pela equipe. Inclua `app/app.py`, `requirements.txt` e `.streamlit/config.toml`. Mantenha `.env`, `secrets.toml`, estados e planos Terraform, certificados locais, caches e bases brutas fora do Git. O aplicativo publicado consulta o banco e dispensa dados processados no repositório.

## Configuração de publicação

Na criação do aplicativo, selecione o repositório, a branch revisada e o arquivo principal `app/app.py`. Em **Advanced settings**, selecione **Python 3.12**. No campo **Secrets**, use a seção abaixo com os valores autorizados. Os campos são exemplos fictícios. Substitua-os antes de iniciar a publicação. [Publicar no Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) · [Configurar Secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)

```toml
[observatorio]
APP_DATA_MODE = "postgres"
DB_HOST = "host-do-servico"
DB_PORT = 5432
DB_NAME = "banco-do-projeto"
DB_USER = "usuario-somente-leitura"
DB_PASSWORD = "preencher-no-painel-de-segredos"
DB_SSLMODE = "verify-full"
DB_SSL_CA_PEM = """
SUBSTITUA_PELO_PEM_DA_CA_DO_PROJETO_AIVEN
"""
```

Valores definidos explicitamente no ambiente têm prioridade sobre a seção `[observatorio]`. `DB_PORT` deve receber a porta real do serviço, que pode diferir do exemplo. Use o hostname do serviço coberto pelo certificado. `DB_SSL_CA_PEM` é o conteúdo PEM da CA do projeto Aiven. O aplicativo o grava temporariamente em um diretório privado enquanto abre a conexão. Como alternativa em ambiente com arquivos locais, use `DB_SSLROOTCERT` com o caminho da CA e deixe `DB_SSL_CA_PEM` ausente. `verify-full` verifica a cadeia e o hostname. O padrão `require` preserva a exigência de TLS para configurações existentes. Configure explicitamente `verify-full` para a publicação. [Certificados TLS da Aiven](https://aiven.io/docs/platform/concepts/tls-ssl-certificates) · [PostgreSQL e Python](https://aiven.io/docs/products/postgresql/howto/connect-python)

Use uma credencial PostgreSQL com acesso de leitura apenas a `public.vw_observatorio_censo_enade`, além das permissões de conexão e acesso ao schema necessárias. As permissões devem ser confirmadas pelo responsável pelo banco. O painel abre a sessão com padrão somente leitura, consulta a view e encerra a conexão. As cargas e o Terraform usam credenciais e fluxos próprios.

## Conferir após publicação autorizada

1. Abra o endereço publicado e confira fonte **PostgreSQL (vw_observatorio_censo_enade)**, seis cartões, tema e três abas. Teste UF presencial, categoria EaD, modalidade, grau, rede, área Cine e correspondência ENADE.
2. No modo `postgres`, o painel lê o banco a cada execução e não usa dados locais se houver falha. Em `auto`, a interface sinaliza a falha de conexão e identifica o CSV quando esse fallback é utilizado. Use `postgres` na demonstração da integração.
3. Compare os valores com o recorte esperado e confira o tempo de resposta e a memória no Community Cloud. A plataforma pode hibernar aplicativos inativos. O plano gratuito da Aiven também pode suspender serviços inativos. Antes da apresentação, confirme que o aplicativo e o banco estão disponíveis. O modo CSV pode servir para ensaio local com a origem visível. [Limites do Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app) · [Aiven PostgreSQL gratuito](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier)

## Pendências com a equipe

- Confirmar o projeto, o serviço PostgreSQL ativo, o plano gratuito, o hostname, a porta e o nome do banco no console Aiven.
- Confirmar a existência da view aprovada, as permissões do usuário de leitura e a CA do projeto. Se houver restrição de rede, conferir a conectividade a partir da hospedagem autorizada. [Rede do Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/status)
- Inserir a senha somente no painel de segredos. A equipe deve revisar a eventual rotação de credenciais anteriormente compartilhadas e coordenar futuras rotações da CA.
- Autorizar o uso do repositório GitHub e a publicação. Validar a conexão, o certificado e o desempenho com a Aiven real em etapa posterior.
