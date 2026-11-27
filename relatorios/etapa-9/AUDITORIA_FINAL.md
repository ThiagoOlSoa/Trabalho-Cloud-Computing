# Auditoria final · Etapa 9

| Área | Resultado da revisão |
|---|---|
| Base e histórico | HEAD remoto da equipe conferido em `a32f4e9`. O commit da Etapa 8 conferido no bundle é `98dc179`. A nova branch avança a partir dele. |
| Granularidade | Uma colisão de códigos ENADE depois da normalização pode multiplicar linhas do recorte. O Streamlit recusa chaves nulas ou repetidas antes de exibir indicadores. O verificador acusa a mesma condição. As fórmulas foram preservadas. |
| Preflight | Conferência de **42 colunas** a partir das referências físicas da consulta final, com checagem de tipos, leitura e permissões de escrita. O teste executa o preflight com o papel restrito e confirma a equivalência da lista. |
| Legado e indicadores | Testes cobrem chaves INTEGER/VARCHAR, seis tabelas, 7.078 cursos distintos, 5.413 sem ENADE e 1.665 com ENADE. A view antiga continua como objeto da fixture para provar que o painel pode operar sem privilégio de leitura nela. |
| Interface | Tema, cartões, filtros e consulta base preservados. A suíte cobre filtros isolados e combinados, vazio, zero, dados indisponíveis, falha em modo PostgreSQL, identificação da fonte e proteção de erros. |
| ETL e dados | Os dois gzip versionados foram lidos pelas cargas. A suíte integrada cobre primeira carga, idempotência, rollback e integridade referencial. |
| Segurança | Revisão de caminhos Git, arquivos de configuração e mensagens de erro. A busca por padrões de token, URIs PostgreSQL autenticadas e blocos de chave privada nos arquivos de texto ficou sem ocorrências. A senha é configurada fora do Git. |
| Documentação | Manual vincula o bundle, detalha o preflight e identifica o papel de leitura. Exemplos de carga apontam para os gzip existentes. Links relativos Markdown conferidos na raiz do checkout. Os documentos Word permanecem identificados como históricos. |
| Terraform e CI | Formatação, inicialização sem backend e validação Terraform passaram localmente. O workflow passou em `actionlint`, e as suítes foram refeitas no clone obtido pelo bundle. O CI hospedado da Etapa 9 depende do PR da equipe. |

O certificado e as permissões efetivas da Aiven real devem ser homologados pelo administrador. Use o roteiro operacional antes de abrir o endereço ao professor. [Manual de implantação](MANUAL_AIVEN_STREAMLIT.md) · [Checklist](CHECKLIST_MANUAL.md)
