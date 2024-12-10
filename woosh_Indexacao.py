import os
import time
import re
from concurrent.futures import ThreadPoolExecutor
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from whoosh.analysis import StemmingAnalyzer
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer



lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))


def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)
    words = text.split()
    processed_words = [
        lemmatizer.lemmatize(word) for word in words if word not in stop_words
    ]

    return processed_words



def create_schema():
    return Schema(
        path=ID(stored=True, unique=True),
        content=TEXT(analyzer=StemmingAnalyzer(), stored=False),
    )



def create_index(index_dir, docs_dir, num_threads=4):
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)
    if not os.listdir(index_dir):
        idx = create_in(index_dir, create_schema())
    else:
        idx = open_dir(index_dir)

    writer = idx.writer(procs=num_threads, multisegment=True)

    total_preprocess_time = 0
    total_indexing_time = 0
    doc_count = 0

    def process_file(file_path):
        nonlocal total_preprocess_time, total_indexing_time, doc_count
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                start_preprocess = time.time()
                processed_content = preprocess_text(content)
                end_preprocess = time.time()
                total_preprocess_time += (end_preprocess - start_preprocess)
                start_indexing = time.time()
                writer.add_document(path=file_path, content=" ".join(processed_content))
                end_indexing = time.time()
                total_indexing_time += (end_indexing - start_indexing)
                doc_count += 1
        except Exception as e:
            print(f"Erro ao processar o arquivo {file_path}: {e}")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for root, _, files in os.walk(docs_dir):
            for file in files:
                file_path = os.path.join(root, file)
                executor.submit(process_file, file_path)

    writer.commit()

    return total_preprocess_time, total_indexing_time, doc_count


def main_indexacao():
    index_dir = os.path.join(os.getcwd(), "index")
    docs_dir = r'C:\Users\zin\Downloads\pan-plagiarism-corpus-2011\external-detection-corpus\source-document'

    print("Iniciando a indexação...")
    total_preprocess_time, total_indexing_time, doc_count = create_index(index_dir, docs_dir, num_threads=4)


    avg_preprocess_time = total_preprocess_time / doc_count if doc_count > 0 else 0
    avg_indexing_time = total_indexing_time / doc_count if doc_count > 0 else 0

    print(f"Documentos processados: {doc_count}")
    print(f"Tempo médio de pré-processamento por documento: {avg_preprocess_time:.4f} segundos")
    print(f"Tempo médio de indexação por documento: {avg_indexing_time:.4f} segundos")


if __name__ == "__main__":
    start_time = time.time()
    main_indexacao()
    end_time = time.time()

    execution_time = end_time - start_time
    minutes = execution_time // 60
    seconds = execution_time % 60

    print(f"Tempo total de execução: {int(minutes)} minutos e {seconds:.2f} segundos")