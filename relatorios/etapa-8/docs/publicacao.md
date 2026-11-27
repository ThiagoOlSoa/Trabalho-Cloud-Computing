# Manual de publicação no Streamlit Community Cloud

Use este manual após a aprovação da publicação. O Community Cloud precisa de acesso a um repositório GitHub com o projeto. O painel pode consultar diretamente as tabelas PostgreSQL com um usuário de leitura. O ambiente de publicação usa a raiz do repositório para localizar o tema e pode dar prioridade ao manifesto ao lado do arquivo principal. Este projeto usa um único `requirements.txt` na raiz. [Organização dos arquivos](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization) · [Dependências](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies)

## Preparar e validar em um computador

1. Extraia o ZIP em uma pasta nova. Compare os hashes com `MANIFESTO_SHA256.txt`. Em Linux, a partir da raiz, use `sha256sum -c MANIFESTO_SHA256.txt`.
2. Crie um ambiente virtual Python 3.12 e ative-o. Instale com `python -m pip install -r requirements.txt` e confira com `python -m pip check`.
3. Execute `python -m streamlit run app/app.py` na raiz para aplicar `.streamlit/config.toml`. Sem fontes configuradas, o painel deve explicar que precisa dos CSVs ou do PostgreSQL. O modo CSV pode usar os dois gzip versionados em `data/processed/`. [Preparação dos dados](../data/README.md)
4. Prepare o repositório e a branch aprovados pela equipe. Inclua `app/app.py`, `sql/cursos.sql`, `requirements.txt` e `.streamlit/config.toml`. Mantenha `.env`, `secrets.toml`, estados e planos Terraform, certificados locais, caches e bases brutas fora do Git. O aplicativo publicado consulta o banco e dispensa dados processados no repositório.

## Configuração de publicação

Em [share.streamlit.io](https://share.streamlit.io/), selecione **Create app** e faça a implantação a partir do GitHub. Escolha `kananda09/Trabalho-Cloud-Computing`, a branch `main` após o merge aprovado e o arquivo principal `app/app.py`. Em **Advanced settings**, selecione **Python 3.12**. No campo **Secrets**, use a seção abaixo com os valores autorizados. Os campos são exemplos fictícios. Substitua-os antes de iniciar a publicação. [Publicar no Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) · [Configurar Secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)

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

Valores definidos explicitamente no ambiente têm prioridade sobre a seção `[observatorio]`. `DB_PORT` deve receber a porta real do serviço, que pode diferir do exemplo. Use o hostname do serviço coberto pelo certificado. `DB_SSL_CA_PEM` é o conteúdo PEM da CA do projeto Aiven. O aplicativo o grava temporariamente em um diretório privado enquanto abre a conexão. Como alternativa em ambiente com arquivos locais, use `DB_SSLROOTCERT` com o caminho da CA e deixe `DB_SSL_CA_PEM` ausente. `verify-full` verifica a cadeia e o hostname. Em modo `postgres`, uma conexão remota exige `verify-full`. [Certificados TLS da Aiven](https://aiven.io/docs/platform/concepts/tls-ssl-certificates) · [PostgreSQL e Python](https://aiven.io/docs/products/postgresql/howto/connect-python)

Use um papel PostgreSQL com `CONNECT`, `USAGE` em `public` e leitura restrita às colunas usadas na consulta compartilhada. Consulte o [preflight](../sql/preflight_painel.sql). As permissões devem ser confirmadas pelo responsável pelo banco. O painel abre a sessão com padrão somente leitura, consulta as tabelas e encerra a conexão. As cargas e o Terraform usam credenciais e fluxos próprios.

## Conferir após publicação autorizada

1. Abra o endereço publicado e confira **PostgreSQL remoto**, **TLS Ativo**, seis cartões e três abas. Teste UF presencial, categoria EaD, modalidade, grau, rede, área Cine e correspondência ENADE.
2. No modo `postgres`, o painel lê o banco a cada execução e não usa dados locais se houver falha. Em `auto`, a interface sinaliza a falha de conexão e identifica o CSV quando esse fallback é utilizado. Use `postgres` na demonstração da integração.
3. Compare os dez [valores de referência](../README.md) com todos os filtros abertos. Confira 7.078 cursos e 1.665 com ENADE.
4. Defina a visibilidade pública do aplicativo, confirme o endereço `.streamlit.app` em uma janela anônima no desktop e no celular e compartilhe o link aprovado com o professor.
5. Confira os resultados com o recorte esperado e confira o tempo de resposta e a memória no Community Cloud. A plataforma pode hibernar aplicativos inativos. O plano gratuito da Aiven também pode suspender serviços inativos. Antes da apresentação, confirme que o aplicativo e o banco estão disponíveis. O modo CSV pode servir para ensaio local com a origem visível. [Limites do Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app) · [Aiven PostgreSQL gratuito](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier)

## Pendências com a equipe

- Confirmar o projeto, o serviço PostgreSQL ativo, o plano gratuito, o hostname, a porta e o nome do banco no console Aiven.
- Confirmar as colunas das seis tabelas, as permissões do usuário de leitura e a CA do projeto. Se houver restrição de rede, conferir a conectividade a partir da hospedagem autorizada. [Rede do Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/status)
- Inserir a senha somente no painel de segredos. A equipe deve revisar a eventual rotação de credenciais anteriormente compartilhadas e coordenar futuras rotações da CA.
- Autorizar o uso do repositório GitHub e a publicação. Validar a conexão, o certificado e o desempenho com a Aiven real em etapa posterior.
