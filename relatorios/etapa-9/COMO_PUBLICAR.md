# Publicar a candidata final no repositório da equipe

O bundle inclui o histórico completo da branch. Use uma conta com acesso de escrita em `kananda09/Trabalho-Cloud-Computing`. Execute após baixar o bundle, substituindo o caminho indicado.

```sh
git clone https://github.com/kananda09/Trabalho-Cloud-Computing.git
cd Trabalho-Cloud-Computing
git bundle verify /caminho/observatorio-etapa-9.bundle
git fetch /caminho/observatorio-etapa-9.bundle refs/heads/etapa-9-entrega-final-streamlit:refs/heads/etapa-9-entrega-final-streamlit
git switch etapa-9-entrega-final-streamlit
git rev-parse --short HEAD
python -m scripts.manifesto_sha256 --check
git diff --stat origin/main...HEAD
git push -u origin etapa-9-entrega-final-streamlit
gh pr create --repo kananda09/Trabalho-Cloud-Computing --base main --head etapa-9-entrega-final-streamlit --title 'Etapa 9 — Entrega final do Observatório' --body 'Consolida e verifica o Streamlit em PostgreSQL legado e CSV. A homologação da Aiven e a publicação serão feitas pela equipe.'
```

O commit esperado é `9eb84b0`. Se a `main` tiver avançado além de `a32f4e9`, a equipe deve revisar a integração no PR. Após a publicação da branch, confira os dois jobs do GitHub Actions e revise o diff antes de aprovar o merge.
