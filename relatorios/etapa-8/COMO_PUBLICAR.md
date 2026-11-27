# Aplicar a versão final da Etapa 8

O bundle é incremental e requer o histórico da `main` de `kananda09/Trabalho-Cloud-Computing`. Ele mantém os nove commits anteriores e acrescenta a revisão com Streamlit como painel exclusivo.

1. Extraia este ZIP.
2. Confirme que sua conta tem permissão de escrita no repositório da equipe.
3. Execute os comandos abaixo, substituindo o caminho do bundle pelo local onde extraiu o ZIP.

```sh
git clone https://github.com/kananda09/Trabalho-Cloud-Computing.git
cd Trabalho-Cloud-Computing
git fetch /caminho/observatorio-etapa8-streamlit.bundle refs/heads/etapa-8-consolidacao-final:refs/heads/etapa-8-consolidacao-final
git switch etapa-8-consolidacao-final
python -m scripts.manifesto_sha256 --check
git log --oneline origin/main..HEAD
git diff --stat origin/main...HEAD
git push -u origin etapa-8-consolidacao-final
gh pr create --repo kananda09/Trabalho-Cloud-Computing --base main --head etapa-8-consolidacao-final --title 'Etapa 8 — Consolidação final com Streamlit' --body 'Consolida o Streamlit como único painel. Validação local com PostgreSQL legado, Terraform e manifesto concluída. CI no destino e conexão real pendentes.'
```

Se a `main` tiver novos commits, confira o diff e resolva conflitos na branch. Use um envio comum, sem forçar. Revise o GitHub Actions no PR. A publicação no Streamlit Community Cloud segue o manual após aprovação do merge e do deploy.
