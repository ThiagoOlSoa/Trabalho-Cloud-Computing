# Apresentação do dashboard

A revisão mantém a paleta azul e verde-petróleo do Observatório. O tema de `.streamlit/config.toml` aplica as cores aos controles do próprio Streamlit. Os estilos locais do cabeçalho e dos cartões usam classes da aplicação e contêineres com chave.

## Leitura e interação

- Os seis cartões mostram o valor, a fonte ou o período e uma explicação no botão de ajuda. A borda dos cartões diferencia valores observados, zeros e base insuficiente. Um traço e a descrição do estado acompanham os indicadores indisponíveis.
- A fonte ativa e o recorte são exibidos acima dos cartões. Os filtros de UF e rótulo Cine ficam agrupados em uma seção que pode ser aberta na barra lateral. As opções iniciais e a categoria “EaD · UF não atribuída” seguem a Etapa 5A.
- A cobertura do ENADE aparece abaixo dos cartões. Ela indica cursos presentes no arquivo. A média usa somente cursos com notas válidas. A seção “Como interpretar os indicadores” reúne os denominadores e limites de interpretação.
- O gráfico de composição usa toda a largura disponível e mantém as três séries da Etapa 5A. Os valores exatos ficam disponíveis ao passar o ponteiro sobre as barras e na tabela expansível. A matriz usa um painel vertical para cada modalidade com dados. As tabelas mantêm seus campos e podem ser roladas horizontalmente em telas estreitas.

## Reprodução local

Execute `streamlit run app/app.py` a partir da raiz do repositório para que o tema local seja aplicado. Use as fontes já descritas na documentação do projeto.

A revisão usou Streamlit 1.67.0 em Chromium. Foram verificadas janelas de 1.440 × 1.000, 390 × 844 e 320 × 740 pixels. Em telas estreitas, os cartões se empilham e a barra lateral abre sobre o conteúdo. A revisão móvel usou emulação de largura no Chromium. Safari e aparelhos físicos ainda podem apresentar diferenças nos controles nativos do Streamlit. Os valores da seleção completa foram conferidos no navegador e a suíte automatizada verificou a paridade com PostgreSQL local.
