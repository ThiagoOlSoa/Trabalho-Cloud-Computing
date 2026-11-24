# Desempenho e operação do Grafana

## Consultas no carregamento

A configuração exportada define **cinco consultas de listas e nove consultas de painéis**, totalizando 14 SELECTs em uma visita completa. O seletor ENADE é uma lista fixa do Grafana e não consulta o banco. O Grafana pode adiar painéis fora da tela, por isso a ordem e a quantidade de solicitações HTTP na abertura variam. Uma alteração de filtro reexecuta os painéis com as novas seleções. A atualização periódica fica desativada.

As listas usam `SELECT DISTINCT` sobre a população de cursos. A lista de UF pode precisar de informações tanto da oferta presencial quanto da modalidade ENADE. Os planos de projeções mais simples podem eliminar junções e agregados que não são usados. As consultas de indicadores agregam o Censo antes das dimensões e do ENADE. As dimensões 1 e 2 produzem 7.078 grupos de curso. A CTE materializada de ENADE calcula a chave uma vez por registro da edição 2023, com 1.665 chaves no ensaio. As quatro partes que usam `indicadores.sql` repetem o recorte em consultas separadas, embora o PostgreSQL possa eliminar expressões não projetadas. Essas repetições são custo por visita, independentemente do número de linhas exibidas.

## Método

O ensaio usa PostgreSQL 16.2 local descartável, CSVs completos, esquema legado simulado e o papel com leitura limitada por coluna. Foi executado `EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON)` em cada SELECT exportado, com todos os filtros abertos. A lista de opções foi preparada antes da cronometragem. O ensaio executa as 14 consultas em série por conexão, com uma conexão para cada visitante simulado. Mede tempo SQL e duração do lote local, com cache aquecido. O ensaio simultâneo tem três conexões e não representa a latência do navegador, a rede ou o hardware do serviço Free.

Para reproduzir, a partir da raiz, com as dependências do projeto e binários PostgreSQL 16:

```sh
MEDIR_GRAFANA=1 bash scripts/testar_postgres_local.sh
```

## Resultados locais

| Cenário | Resultado |
|---|---:|
| Cinco listas | 32,5–37,2 ms por consulta |
| Nove painéis | 47,0–93,2 ms por consulta |
| Um visitante | Mediana de 48,4 ms por consulta, 715 ms no lote |
| Três visitantes simultâneos | Mediana de 104,7 ms por consulta, lotes de 1.327 a 1.848 ms por visitante |

As listas registraram entre 2.931 e 3.032 acertos de buffers compartilhados por consulta. Os painéis registraram entre 39.224 e 40.172. Nesse ensaio os planos não precisaram ler blocos de disco. Esses números contam acessos a buffers, incluindo acessos repetidos ao mesmo bloco. O agrupamento por população foi o painel mais caro da rodada. Com três visitantes, a mediana por consulta mais que dobrou, mesmo com uma conexão por visitante. Em produção, confirme o efeito do pool e do agendamento dos painéis do Grafana na latência percebida.

## Uso no Aiven PostgreSQL Free

- Comece com **3 conexões abertas e 1 ociosa** no pool Grafana. Conte as outras aplicações e sessões da equipe na capacidade total. Mantenha atualização periódica desativada e combine um ensaio com os acessos do professor para verificar fila, tempo de resposta e erros.
- Antes de otimizar, confirme o desempenho real com a equipe após autorização. A mesma consulta pode escolher outro plano por volume, estatísticas ou concorrência. Se o volume de visitas aumentar, investigue a possibilidade de compartilhar consultas entre painéis e simplificar listas que não dependem da cobertura, com testes de paridade para evitar perder cursos sem ENADE ou alterar regras de UF.
- Confira primeiro os índices existentes. O esquema de referência já tem `(nu_ano_censo, co_curso, tp_dimensao, id_localizacao)` no fato Censo e chave `(nu_ano, co_curso)` no ENADE. Para o recorte integral, uma leitura sequencial pode ser mais barata do que usar um índice quando o predicado seleciona grande parte do Censo.

### Mudanças sob responsabilidade do administrador

Se os planos reais indicarem custo em seleções restritas, compare em ambiente descartável um índice B-tree com fatores iniciais `(nu_ano_censo, tp_dimensao, co_curso)`. Para crescimento histórico do ENADE, investigue um índice por edição e chave normalizada apenas se a consulta for adaptada para aproveitá-lo e os dados permanecerem únicos. Com 1.665 registros e materialização por edição, o benefício pode ser pequeno. Medir primeiro evita custo extra de armazenamento e escrita no plano Free. Qualquer criação de índice, alteração de estatísticas ou mudança no banco compartilhado depende de autorização do administrador.

## CI e verificações

O workflow separa a suíte sem banco da suíte com PostgreSQL 16 descartável. As duas usam Python 3.12. O job integrado instala os binários, inicializa um cluster novo por socket Unix e o remove no fim. Os dois CSVs gzip do repositório são descompactados em diretório temporário. Cada job publica contagens e os testes ignorados no resumo do GitHub Actions. A verificação de caminhos do Git recusa arquivos de configuração sensível, estado Terraform, chaves e dados brutos. Ela cobre caminhos de arquivos e deve ser acompanhada de revisão de segredos embutidos em arquivos permitidos.
