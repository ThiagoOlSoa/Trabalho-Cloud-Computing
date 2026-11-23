# Terraform — PostgreSQL Aiven Free (Etapa 3)

**Estado:** configuração declarativa pronta para validação local. **Nenhum recurso foi criado, importado, destruído ou atualizado.** A integração operacional depende de autorização e das informações do responsável pela conta Aiven.

## 1. Escopo e compatibilidade

- Provedor oficial: [`aiven/aiven`](https://registry.terraform.io/providers/aiven/aiven/latest/docs), faixa `>= 4.0.0, < 5.0.0`.
- Terraform CLI: `>= 1.5.0, < 2.0.0`.
- Recurso único: `aiven_pg.observatorio`, no projeto Aiven **já existente**, com `plan = "free-1-1gb"` (identificador do PostgreSQL gratuito no catálogo público da Aiven. Confirme a disponibilidade no projeto e na organização antes de operar).
- Sem `cloud_name`, VPC, IPs estáticos, armazenamento adicional, pooling, integração de serviços nem recursos pagos. A região do plano Free é atribuída pela Aiven.
- `lifecycle.prevent_destroy = true` protege contra destruição/substituição propostas enquanto o bloco continuar presente. **Não impede** remoção manual, alterações fora do Terraform nem todas as falhas operacionais.
- Este Terraform gerencia infraestrutura, **não** cria tabelas, aplica `sql/`, carrega dados do INEP ou configura o dashboard. Os scripts existentes usam `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` e `DB_SSLMODE` separados do token Aiven.

> **Limites do Free**: 1 CPU, 1 GB RAM e 1 GB disco; sem integrações nativas, VPC, IP fixo ou connection pooling; limite de 20 conexões. Confirmar disponibilidade e limite de um PostgreSQL gratuito por organização. Usar conexão TLS e um usuário somente leitura no dashboard, conforme a Etapa 2.

Fontes oficiais consultadas (novembro/2026):
- [Aiven — catálogo público de planos](https://api.aiven.io/v1/service_types)
- [Terraform Registry — autenticação do provedor](https://registry.terraform.io/providers/aiven/aiven/latest/docs#environment-variables)
- [Aiven — plano gratuito PostgreSQL](https://aiven.io/docs/products/postgresql/concepts/pg-free-tier)
- [Aiven — introdução PostgreSQL/Terraform](https://aiven.io/docs/products/postgresql/get-started)
- [Terraform Registry — recurso aiven_pg](https://registry.terraform.io/providers/aiven/aiven/latest/docs/resources/pg)
- [Terraform Registry — importação de recursos existentes](https://registry.terraform.io/providers/aiven/aiven/latest/docs/guides/importing-resources)

## 2. Arquivos

| Arquivo | Responsabilidade |
|---|---|
| `versions.tf` | Requisitos de Terraform CLI e provedor Aiven |
| `main.tf` | Provedor Aiven e serviço PostgreSQL Free; proteção contra destruição |
| `variables.tf` | Identificação não sensível do projeto e serviço |
| `outputs.tf` | Somente identificação, sem URI nem senha |
| `terraform.tfvars.example` | Exemplo fictício, sem token, para cópia local |

## 3. Preparação local SEM acessar a Aiven

1. Instale Terraform CLI 1.5 ou superior (menor que 2.0).
2. No diretório `terraform/`, copie `terraform.tfvars.example` para `terraform.tfvars` e preencha com **nomes reais apenas quando autorizados**. Esse arquivo é excluído por `.gitignore`.
3. Para verificar somente sintaxe/estrutura e instalar o provedor, execute:

   ```sh
   terraform fmt -check -recursive
   terraform init -backend=false
   terraform validate
   ```

   `init -backend=false` baixa o provedor da Registry, mas **não** acessa a conta Aiven e **não** cria serviço. A inicialização pode produzir `.terraform/` e `.terraform.lock.hcl` locais. Confira a versão escolhida e proteja o diretório de trabalho.

4. Não execute `terraform plan` sem antes confirmar projeto/serviço e a estratégia abaixo. **Um plano que mostre `+ create` não é evidência de que a instância existente será preservada.**

## 4. Autenticação (apenas quando autorizada)

Use um token Aiven da equipe com privilégios mínimos adequados, injetado **somente** pela variável de ambiente `AIVEN_TOKEN`. Não o inclua em `terraform.tfvars`, arquivos `.tf`, logs públicos, capturas de tela ou chat. O token é diferente da senha PostgreSQL (`DB_PASSWORD`). Não compartilhar ou versionar o estado (`terraform.tfstate`, backups) — ele pode conter senhas de serviço mesmo quando outputs são inocentes.

Sugestão para shell compatível com Bash, executado pelo responsável no próprio terminal:

```sh
read -r -s -p "Token Aiven: " AIVEN_TOKEN; echo
export AIVEN_TOKEN
```

Ao encerrar a sessão: `unset AIVEN_TOKEN`. Em outros shells, configure a variável pelo mecanismo de secrets apropriado, sem gravá-la em arquivo versionado.

## 5. Cenário A — serviço PostgreSQL JÁ existe (preferencial)

**Não executar nesta etapa. Passos futuros, dependentes de autorização do administrador.**

1. Verificar na Console Aiven: nome exato do projeto, nome exato do serviço, plano **realmente gratuito**, estado, tamanho usado e responsável. Confirmar que ninguém está gerenciando a mesma instância em outro estado Terraform.
2. Solicitar backup recente e preservar cópia segura de qualquer estado Terraform preexistente. Confirmar com a equipe a decisão de colocar o serviço sob gerenciamento deste código.
3. Preencher localmente `terraform.tfvars` com os dois nomes exatos e definir `AIVEN_TOKEN` no ambiente. Não compartilhar o token.
4. Inicializar Terraform. Importar **somente com aprovação explícita** e sem mudança de configurações; o ID no formato oficial é `PROJETO/SERVICO`:

   ```sh
   terraform import aiven_pg.observatorio PROJETO/SERVICO
   ```

5. Depois da importação, comparar as propriedades do estado com o serviço real e revisar `terraform plan` detalhadamente. **Se mostrar criação, atualização de plano, substituição ou destruição: PARAR. Não aplicar.** Corrigir o código ou o processo de importação com o administrador antes de prosseguir.
6. Guardar o `tfstate` com proteção adequada; lembrar que estado local com dados sensíveis não deve ser enviado ao GitHub nem em ZIPs.

> Importar associa o serviço existente ao estado Terraform; não é a mesma operação que criar um serviço novo. O comando pode acessar a API Aiven e atualizar o **estado local**. A equipe deve autorizá-lo mesmo que ele não provisione serviços.

## 6. Cenário B — serviço não existe

**Não executar nesta etapa.** Só considerar após o administrador confirmar que não existe um PostgreSQL a preservar, que o projeto Aiven já existe e que a organização ainda pode ter um PostgreSQL gratuito.

1. Confirmar na Console Aiven os planos realmente disponíveis e o identificador exato do plano gratuito (`free-1-1gb`) e o tamanho de 1 GB.
2. Definir nome único do novo serviço e colocar os nomes no `terraform.tfvars` local.
3. Autorizar token pelo ambiente. Inspecionar cuidadosamente `terraform plan`: ele deve mostrar **exatamente um PostgreSQL Free** a criar, sem serviços adicionais, plano pago ou alterações destrutivas.
4. **Somente em etapa futura e com aprovação explícita**, considerar `terraform apply`. Nunca executar automaticamente e jamais trocar o plano para pago para contornar indisponibilidade.

> `terraform plan` consulta o serviço remoto e pode apresentar informações sensíveis no terminal. Revise antes de compartilhar saídas.

## 7. Riscos e política de não destruição

- `prevent_destroy` não equivale a uma política de backup e não protege se alguém remover o bloco da configuração e aplicar um plano posterior.
- `terraform destroy`, `terraform apply`, `terraform import`, migrações SQL e criação de serviços **não foram executados nesta etapa**.
- Não use `-auto-approve` nem `-target` para contornar um plano inesperado.
- Antes de qualquer operação real, o administrador deve confirmar o plano gratuito, a titularidade do serviço, a ausência de outro estado Terraform gerenciando-o e a preservação de dados.
- A Aiven pode suspender serviços gratuitos inativos. O Free não oferece integrações nativas entre serviços; a ligação Python/Streamlit → PostgreSQL ocorre por conexão SQL, não por integração nativa da plataforma.
- Se for necessário demonstrar dois serviços Aiven ao professor, alinhe a exigência e as limitações do Free antes de ampliar a infraestrutura. **Esta implementação não cria Kafka/OpenSearch/MySQL.**

## 8. Informações a solicitar aos colegas (sem segredos)

- Nome exato do projeto Aiven.
- Nome exato do serviço PostgreSQL e confirmação se ainda existe.
- Tier e identificador do plano mostrado na Console, capacidade e armazenamento usado.
- Situação atual do serviço (`RUNNING`/`POWEROFF`) e se o projeto já está sendo gerenciado por Terraform.
- Pessoa responsável pela conta/serviço e autorização para uma possível importação.
- Confirmação de que a senha divulgada anteriormente foi rotacionada, se aplicável (**sem solicitar a senha**).

**Não solicitar por chat:** `AIVEN_TOKEN`, `DB_PASSWORD`, `service_uri` com credenciais, conteúdo de `.env`, arquivos `.tfstate` ou certificados privados.
