import os
import time
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk, BulkIndexError



es = Elasticsearch("http://localhost:9200")

def read_large_file(file_path):

    with open(file_path, 'r', encoding='utf-8') as f:
        content = ""
        for line in f:
            content += line
        return content



def index_documents(folder_path, index_name):
    actions = []
    total_preprocessing_time = 0
    total_indexing_time = 0
    total_documents = 0


    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".txt"):

                start_preprocessing_time = time.time()
                content = read_large_file(os.path.join(root, file))
                preprocessing_time = time.time() - start_preprocessing_time
                total_preprocessing_time += preprocessing_time


                action = {
                    "_index": index_name,
                    "_source": {
                        "filename": file,
                        "content": content
                    }
                }
                actions.append(action)
                total_documents += 1


                if len(actions) >= 50:
                    try:
                        start_indexing_time = time.time()
                        bulk(es, actions)
                        indexing_time = time.time() - start_indexing_time
                        total_indexing_time += indexing_time
                        actions = []  # Limpar ações
                    except BulkIndexError as e:
                        print(f"Erro durante a indexação em massa: {e}")
                        continue  #

    if actions:
        try:
            start_indexing_time = time.time()
            bulk(es, actions)
            indexing_time = time.time() - start_indexing_time
            total_indexing_time += indexing_time
        except BulkIndexError as e:
            print(f"Erro durante a indexação final: {e}")

    avg_preprocessing_time = total_preprocessing_time / total_documents if total_documents else 0
    avg_indexing_time = total_indexing_time / total_documents if total_documents else 0

    # Exibir os resultados
    print(f"Tempo médio de pré-processamento por documento: {avg_preprocessing_time:.4f} segundos")
    print(f"Tempo médio de indexação por documento: {avg_indexing_time:.4f} segundos")

    return avg_preprocessing_time, avg_indexing_time


if __name__ == "__main__":
    start_time = time.time()
    folder_path = r'C:\Users\zin\Downloads\pan-plagiarism-corpus-2011\external-detection-corpus\source-document'  # Atualize com o caminho correto da sua pasta
    index_name = 'index'

    index_documents(folder_path, index_name)
    end_time = time.time()

    execution_time = end_time - start_time
    minutes = execution_time // 60
    seconds = execution_time % 60

    print(f"Tempo total de execução: {int(minutes)} minutos e {seconds:.2f} segundos")
