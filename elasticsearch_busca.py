import os
import time
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from collections import Counter
from elasticsearch import Elasticsearch
import matplotlib.pyplot as plt
import json
import glob


es = Elasticsearch("http://localhost:9200")


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


def expand_with_synonyms(word, max_synonyms=5):
    synonyms = set()
    count = 0
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name())
            count += 1
            if count >= max_synonyms:
                break
        if count >= max_synonyms:
            break
    return synonyms


def preprocess_approach_4(content, stop_words, top_n_terms):
    tokens = word_tokenize(content.lower())

    tokens = [word for word in tokens if word.isalnum()]

    term_frequencies = Counter(tokens)

    most_frequent_terms = [term for term, freq in term_frequencies.most_common(top_n_terms)]

    expanded_terms = set(most_frequent_terms)
    for term in most_frequent_terms:
        expanded_terms.update(expand_with_synonyms(term))

    return expanded_terms


def preprocess_approach_6(content, stop_words, top_n_terms):
    tokens = word_tokenize(content.lower())
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words]

    term_frequencies = Counter(tokens)

    most_frequent_terms = [term for term, freq in term_frequencies.most_common(top_n_terms)]


    expanded_terms = set(most_frequent_terms)
    for term in most_frequent_terms:
        expanded_terms.update(expand_with_synonyms(term))

    return expanded_terms


def search_documents(file_paths, index_name, approach, top_n_terms=10):
    total_preprocessing_time = 0
    total_queries = 0
    total_documents_found = 0
    results = []

    stop_words = set(stopwords.words("english"))

    for file_path in file_paths:
        if not os.path.exists(file_path):
            print(f"Caminho inválido ou arquivo não encontrado: {file_path}")
            continue

        total_queries += 1

        start_preprocessing_time = time.time()


        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()


        if approach == 4:
            expanded_terms = preprocess_approach_4(content, stop_words, top_n_terms)
        elif approach == 6:
            expanded_terms = preprocess_approach_6(content, stop_words, top_n_terms)
        else:
            raise ValueError("Abordagem inválida. Escolha 4 ou 6.")

        preprocessing_time = time.time() - start_preprocessing_time
        total_preprocessing_time += preprocessing_time

        expanded_terms = list(expanded_terms)[:top_n_terms]

        query_body = {
            "query": {
                "bool": {
                    "should": [
                        {"match": {"content": term}} for term in expanded_terms
                    ]
                }
            },
            "size": 10
        }

        start_search_time = time.time()
        try:
            response = es.options(request_timeout=100).search(index=index_name, body=query_body)  # Ajustando timeout
        except Exception as e:
            print(f"Erro ao realizar a busca: {e}")
            continue

        search_time = time.time() - start_search_time
        seen_files = set()
        total_hits = 0


        retrieved_docs = []
        for hit in response['hits']['hits']:
            doc_file_name = hit['_source']['filename']
            score = hit['_score']
            if doc_file_name not in seen_files:
                retrieved_docs.append({'filename': doc_file_name, 'score': score})
                seen_files.add(doc_file_name)
                total_hits += 1

        total_documents_found += total_hits

        results.append({
            "file": file_path,
            "expanded_terms": list(expanded_terms),
            "retrieved_documents": retrieved_docs,
            "search_time": search_time,
            "total_hits": total_hits
        })


    avg_preprocessing_time = total_preprocessing_time / total_queries if total_queries else 0
    print(f"\nTempo médio de pré-processamento por consulta: {avg_preprocessing_time:.4f} segundos")
    print(f"\nTotal de documentos encontrados em todas as consultas: {total_documents_found}")

    return results


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

	base_path = "C:\\Users\\zin\\Downloads\\pan-plagiarism-corpus-2011\\external-detection-corpus\\suspicious-document"
	file_paths = glob.glob(os.path.join(base_path, "part*", "*.txt"))
    index_name = "index"
   
    retrieved_documents_approach4 = search_documents(file_paths, index_name, approach=4, top_n_terms=10)
    retrieved_documents_approach6 = search_documents(file_paths, index_name, approach=6, top_n_terms=10)
   
    directory = r'C:\Users\zin\Downloads\pan-plagiarism-corpus-2011'
    relevant_documents = get_suspicious_documents(directory, limit=64)

    calculoPrecision(relevant_documents, retrieved_documents_approach4, retrieved_documents_approach6)
