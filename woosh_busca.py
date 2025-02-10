import json
import os
import time
import nltk
import re
import matplotlib.pyplot as plt
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
from nltk.corpus import stopwords, wordnet
from nltk.tokenize import word_tokenize
from collections import Counter


nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')


def get_suspicious_documents(directory_path, limit=64):
    relevant_documents = []
    count = 0

    for filename in os.listdir(directory_path):
        if filename.endswith('.json'):
            file_path = os.path.join(directory_path, filename)

            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if item.get('type') == "suspicious-document":
                            src_file = item.get('src_file', [])
                            relevant_documents.append({'filename': filename, 'src_file': src_file})
                            count += 1

                        if count >= limit:
                            return relevant_documents

                elif isinstance(data, dict):
                    if data.get('type') == "suspicious-document":
                        src_file = data.get('src_file', [])
                        relevant_documents.append({'filename': filename, 'src_file': src_file}) 
                        count += 1
                    if count >= limit:
                        return relevant_documents

    return relevant_documents


def tokenize(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    tokens = word_tokenize(text)
    return tokens


def remove_stopwords(tokens):
    stop_words = set(stopwords.words('english'))
    return [word for word in tokens if word not in stop_words]


def get_synonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
    return synonyms


def expand_with_synonyms(tokens):
    expanded_tokens = []
    for token in tokens:
        synonyms = get_synonyms(token)
        if synonyms:
            expanded_tokens.extend(list(synonyms))
        else:
            expanded_tokens.append(token)
    return expanded_tokens


def partition_by_frequency(tokens):
    freq = Counter(tokens)
    return freq


def approach_4(text):
    tokens = tokenize(text)
    freq = partition_by_frequency(tokens)
    expanded_tokens = expand_with_synonyms(tokens)
    return expanded_tokens, freq


def approach_6(text):
    tokens = tokenize(text)
    tokens = remove_stopwords(tokens)  
    freq = partition_by_frequency(tokens)
    expanded_tokens = expand_with_synonyms(tokens)
    return expanded_tokens, freq


def preprocess_text(query_doc, remove_stopwords_flag=True, expand_synonyms_flag=True):
    tokens = tokenize(query_doc)

    if remove_stopwords_flag:
        tokens = remove_stopwords(tokens)

    if expand_synonyms_flag:
        tokens = expand_with_synonyms(tokens)
    return tokens[:50]


def search_document(searcher, query_parser, query_doc, top_n=5):
    start_time = time.time()
    tokens = preprocess_text(query_doc)
    query_string = ' '.join(tokens)
    q = query_parser.parse(query_string)

    results = searcher.search(q, limit=top_n)
    end_time = time.time()

    print(f"Busca concluída em {end_time - start_time:.2f} segundos")

    unique_results = []
    seen_paths = set()
    for hit in results:
        if hit['path'] not in seen_paths:
            unique_results.append(hit)
            seen_paths.add(hit['path'])
    return unique_results


def main_busca():

    index_dir = r"C:\Users\zin\PycharmProjects\PythonProject1\index"
    base_path = "C:\\Users\\zin\\Downloads\\pan-plagiarism-corpus-2011\\external-detection-corpus\\suspicious-document"

    documentos = []
    for i in range(1, 23):  # Part1 até Part22
        part_dir = os.path.join(base_path, f"part{i}")
        arquivos = glob.glob(os.path.join(part_dir, "suspicious-document*.txt"))
        documentos.extend(arquivos)
    
    ix = open_dir(index_dir)
    searcher = ix.searcher()
    query_parser = QueryParser("content", ix.schema)

    for doc_path in documentos:
        print(f"\nIniciando a busca para o arquivo: {doc_path}...")
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                query_doc = f.read()
            results = search_document(searcher, query_parser, query_doc)
            for hit in results:
                print(f"Documento: {hit['path']}, Similaridade: {hit.score}")
        except FileNotFoundError:
            print(f"Erro: O arquivo {doc_path} não foi encontrado.")
        except Exception as e:
            print(f"Erro ao processar {doc_path}: {e}")
    searcher.close()

def calculate_precision_recall_at_k(relevant_documents, retrieved_documents, k_values):
    relevant_files = []

    for doc in relevant_documents:
        relevant_files.extend(doc['src_file'])

    precision_results = []
    recall_results = []

    for k in k_values:
        retrieved_files_at_k = []

        for doc in retrieved_documents:
            retrieved_files_at_k.extend([doc['filename'] for doc in doc['retrieved_documents']][:k])

        relevant_retrieved = set(relevant_files).intersection(set(retrieved_files_at_k))
        relevant_retrieved_count = len(relevant_retrieved)

        precision = relevant_retrieved_count / len(retrieved_files_at_k) if len(retrieved_files_at_k) > 0 else 0

        recall = relevant_retrieved_count / len(relevant_files) if len(relevant_files) > 0 else 0

        precision_results.append(precision)
        recall_results.append(recall)

    return precision_results, recall_results


def calculoPrecision(relevant_documents, retrieved_documents_approach4, retrieved_documents_approach6):

    k_values = [2, 4, 6, 8, 10]

    precision_results_4, recall_results_4 = calculate_precision_recall_at_k(relevant_documents, retrieved_documents_approach4, k_values)

    precision_results_6, recall_results_6 = calculate_precision_recall_at_k(relevant_documents, retrieved_documents_approach6, k_values)

    plt.figure(figsize=(10, 6))
    plt.plot(k_values, precision_results_4, marker='o', label='Abordagem 4', color='b')
    plt.plot(k_values, precision_results_6, marker='o', label='Abordagem 6', color='g')
    plt.xlabel('k')
    plt.ylabel('Precision at k (P@k)')
    plt.title('Precision at k (P@k) para as abordagens 4 e 6')
    plt.legend()
    plt.grid(True)
    plt.show()

    plt.figure(figsize=(10, 6))
    plt.plot(k_values, recall_results_4, marker='o', label='Abordagem 4', color='b')
    plt.plot(k_values, recall_results_6, marker='o', label='Abordagem 6', color='g')
    plt.xlabel('k')
    plt.ylabel('Recall at k (R@k)')
    plt.title('Recall at k (R@k) para as abordagens 4 e 6')
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    start_time = time.time()
    main_busca()
    end_time = time.time()

    execution_time = end_time - start_time
    minutes = execution_time // 60
    seconds = execution_time % 60

    print(f"Tempo total de execução: {int(minutes)} minutos e {seconds:.2f} segundos")