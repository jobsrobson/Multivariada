# ETL + EDA - Acidentes de Trânsito nas Rodovias da RIDE-DF (2024)

Felipe Toledo, Robson Ricardo, Victor Kauan - Para a disciplina de Análise Multivariada (2°/2025).


## Relatório do Processo de ETL da Base de Acidentes de Trânsito na RIDE-DF

O presente relatório descreve o processo de Extração, Transformação e Carga (ETL) realizado sobre a base de dados de acidentes de trânsito disponibilizada pela Polícia Rodoviária Federal (PRF). O objetivo do tratamento foi preparar os dados para análises exploratórias e inferenciais voltadas à avaliação da infraestrutura viária e dos fatores socioeconômicos relacionados aos acidentes ocorridos nos municípios que compõem a Região Integrada de Desenvolvimento do Distrito Federal e Entorno (RIDE-DF), especificamente aqueles atravessados por rodovias federais.

### 1. Extração

A etapa de extração consistiu no acesso ao dataset original da PRF referente ao ano de 2024. A base foi disponibilizada em formato CSV, contendo registros detalhados de ocorrências em todo o território nacional. Cada linha corresponde a uma ocorrência, contendo atributos relacionados à localização do acidente, condições da via, características meteorológicas, tipo de acidente, veículos envolvidos e consequências às vítimas.

### 2. Transformação

A fase de transformação foi subdividida em várias operações de limpeza, filtragem e padronização, a fim de garantir consistência, coerência semântica e adequação ao escopo da pesquisa.

#### 2.1 Filtragem Geográfica

Foram selecionados apenas os municípios pertencentes à RIDE-DF que possuem rodovias federais em seus limites territoriais.

Essa filtragem reduziu significativamente o volume de dados, restringindo o escopo espacial às áreas diretamente relacionadas à integração rodoviária da região.

#### 2.2 Tratamento de Tipos de Dados

- Conversão de campos de data (data_inversa) e hora (horario) para formatos datetime.
- Conversão de campos numéricos (latitude, longitude, idade, ano de fabricação de veículos) para tipos adequados (float ou int).
- Padronização dos campos relacionados a vítimas (ilesos, feridos_leves, feridos_graves, mortos), convertendo-os para inteiros.

#### 2.3 Criação de Novos Atributos

- Total de vítimas por ocorrência (total_vitimas), obtido pela soma de feridos leves, graves e mortos.
- Indicador binário de vítimas (tem_vitimas), indicando se a ocorrência resultou em ao menos uma vítima.


#### 3.4 Normalização e Limpeza de Outliers

- Limitação da idade dos motoristas a valores plausíveis (0 a 100 anos).
- Restrição do ano de fabricação de veículos ao intervalo entre 1970 e o ano corrente.
- Limitação de registros inconsistentes ou que apresentavam valores anômalos (e.g., idades de 999 anos ou veículos fabricados no ano 0).


#### 3.5 Agregações

- Criação de tabelas agregadas por município, contendo número total de acidentes, total de vítimas e total de mortos.
- Preparação de versão agregada por ocorrência (id), para evitar contagens duplicadas de vítimas quando o dado é registrado por envolvido.

### 4. Carga

A etapa de carga consistiu na disponibilização da base transformada em dois formatos:

- DataFrame estruturado (em ambiente Python/Streamlit), permitindo análises estatísticas e visuais.
- Arquivos CSV derivados (acidentes por município, distribuição temporal, severidade etc.), visando facilitar a reprodutibilidade das análises.

Esses dados foram, em seguida, integrados a um dashboard interativo em Streamlit, que apresenta indicadores, tabelas e visualizações gráficas para apoio a análises acadêmicas.


## 📖 Dicionário de Variáveis

| **Nome da variável**       | **Descrição** |
|-----------------------------|---------------|
| `id`                       | Variável com valores numéricos, representando o identificador do acidente. |
| `data_inversa`              | Data da ocorrência no formato dd/mm/aaaa. |
| `dia_semana`                | Dia da semana da ocorrência. Ex.: Segunda, Terça, etc. |
| `horario`                   | Horário da ocorrência no formato hh:mm:ss. |
| `uf`                        | Unidade da Federação. Ex.: MG, PE, DF, etc. |
| `br`                        | Variável com valores numéricos, representando o identificador da BR do acidente. |
| `km`                        | Identificação do quilômetro onde ocorreu o acidente, com valor mínimo de 0,1 km e casas decimais separadas por ponto. |
| `municipio`                 | Nome do município de ocorrência do acidente. |
| `causa_acidente`            | Identificação da causa principal do acidente. Acidentes com a variável igual a “Não” foram excluídos. |
| `tipo_acidente`             | Identificação do tipo de acidente. Ex.: Colisão frontal, Saída de pista. Acidentes com ordem maior ou igual a 2 foram excluídos. |
| `classificacao_acidente`    | Classificação quanto à gravidade do acidente: Sem Vítimas, Com Vítimas Feridas, Com Vítimas Fatais e Ignorado. |
| `fase_dia`                  | Fase do dia no momento do acidente. Ex.: Amanhecer, Pleno dia, etc. |
| `sentido_via`               | Sentido da via considerando o ponto de colisão: Crescente e Decrescente. |
| `condicao_metereologica`    | Condição meteorológica no momento do acidente: Céu claro, chuva, vento, etc. |
| `tipo_pista`                | Tipo da pista considerando a quantidade de faixas: Dupla, simples ou múltipla. |
| `tracado_via`               | Descrição do traçado da via. |
| `uso_solo`                  | Descrição sobre as características do local do acidente: Urbano = Sim; Rural = Não. |
| `latitude`                  | Latitude do local do acidente em formato geodésico decimal. |
| `longitude`                 | Longitude do local do acidente em formato geodésico decimal. |
| `pessoas`                   | Total de pessoas envolvidas na ocorrência. |
| `mortos`                    | Total de pessoas mortas envolvidas na ocorrência. |
| `feridos_leves`             | Total de pessoas com ferimentos leves envolvidas na ocorrência. |
| `feridos_graves`            | Total de pessoas com ferimentos graves envolvidas na ocorrência. |
| `feridos`                   | Total de pessoas feridas envolvidas na ocorrência (soma de feridos leves e graves). |
| `ilesos`                    | Total de pessoas ilesas envolvidas na ocorrência. |
| `ignorados`                 | Total de pessoas envolvidas na ocorrência cujo estado físico não foi identificado. |
| `veiculos`                  | Total de veículos envolvidos na ocorrência. |
