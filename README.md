# Motores de Busca: ElasticSearch e Whoosh

Este projeto explora a implementação de motores de busca utilizando **ElasticSearch** e **Whoosh**.  
Cada motor de busca inclui um processo de **indexação** e **busca** para permitir a recuperação eficiente de informações. 


## 📌 Arquitetura do Projeto

O fluxo do projeto segue as seguintes etapas:

1. **Leitura de consultas**: O sistema recebe uma consulta do usuário.
2. **Pré-processamento**: Normaliza e limpa os termos da consulta.
3. **Extração de termos da consulta**: Identifica palavras-chave relevantes.
4. **Busca**: O motor de busca (Whoosh ou ElasticSearch) é utilizado para buscar os documentos relevantes.
5. **Ranqueamento da consulta**: Os resultados são organizados por relevância.
6. **Leitura dos documentos**: Os documentos indexados são recuperados.
7. **Pré-processamento dos documentos**: Os textos são normalizados antes da indexação.
8. **Representação e indexação**: Os documentos são armazenados no formato adequado para busca eficiente.
9. **Avaliação dos resultados**: O desempenho da busca é analisado com métricas de relevância.

## 🛠 Tecnologias Utilizadas

- **Python**
- **Whoosh**
- **ElasticSearch**

## 📈 Avaliação dos Resultados

O desempenho dos motores de busca pode ser avaliado com métricas como:

- **Precisão** 🎯
- **Recall** 📊

A coleção é composta por 434.409.077 palavras no total.

Gráfico de Zipf

![Image](https://github.com/user-attachments/assets/4366f692-e9ed-4616-b22c-63e303883bd3)





