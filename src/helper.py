from langchain.embeddings import HuggingFaceEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.document_loaders import (
    PyPDFLoader,
    DirectoryLoader,
    Docx2txtLoader,
    CSVLoader,
    UnstructuredPowerPointLoader as PPTLoader,
    UnstructuredExcelLoader,
    SeleniumURLLoader)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from glob import glob
import logging 
from pathlib import Path
from argparse import Namespace
import yaml
from spire.doc import Document
# import os

def start_logger(config):
    logger_path = config.logger_path
    Path(logger_path).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s %(levelname)s %(name)s %(lineno)s %(message)s',
        handlers= [logging.FileHandler(logger_path),
                   logging.StreamHandler()]
        )
    return logging

def data_with_extension_loader(data, ext, loader, final_documents):
    logger.info('file:%s', data)
    data_loader = DirectoryLoader(data,
                             glob=f'*.{ext}',
                             loader_cls=loader)
    final_documents.extend(data_loader.load())
    # for file in glob(f'data/*.{ext}'):
    #     Path(file).unlink()
    return final_documents

def extension_checker(dir_, ext):
    return glob(f'{dir_}/*.{ext}')

# Extract data from the pdf
def load_data(data):
    final_documents = []
    if isinstance(data, list):
        loader = SeleniumURLLoader(urls=data)
        data = loader.load()
        print('data**: ', data)
        final_documents.extend(data)
    else:
        pdf_files_present = extension_checker(data, 'pdf')
        docx_files_present = extension_checker(data, 'docx')
        csv_files_present = extension_checker(data, 'csv')
        ppt_files_present = extension_checker(data, 'pptx')
        xlsx_files_present = extension_checker(data, 'xlsx')
        doc_files_present = extension_checker(data, 'doc')
        if pdf_files_present:
            final_documents = data_with_extension_loader(data, 'pdf', PyPDFLoader,
                                                final_documents)
        if docx_files_present:
            final_documents = data_with_extension_loader(data, 'docx',
                                                        Docx2txtLoader,
                                                        final_documents)
        if csv_files_present:
            final_documents = data_with_extension_loader(data, 'csv',
                                                        CSVLoader,
                                                        final_documents)
        if ppt_files_present:
            final_documents = data_with_extension_loader(data, 'pptx',
                                                        PPTLoader,
                                                        final_documents)
        if xlsx_files_present:
            final_documents = data_with_extension_loader(data,
                                                        'xlsx',
                                                        UnstructuredExcelLoader,
                                                        final_documents)
        if doc_files_present:
            for doc_file in doc_files_present:
                try:
                    doc = Document()
                    doc.LoadFromFile(doc_file)
                    final_documents = doc.GetText()
                except Exception as e:
                    logger.error(f"Error loading document '{doc_file}': {e}")
    return final_documents


# create text chunks
def text_split(extracted_data, config):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap)
    if isinstance(extracted_data, str):
        text_chunks = text_splitter.create_documents(extracted_data)
    else:
        text_chunks = text_splitter.split_documents(extracted_data)
    return text_chunks

# download embedding model
def download_hugging_face_embeddings(config):
    embeddings = HuggingFaceEmbeddings(
        model_name=config.embeddings1)
    return embeddings

def download_google_embeddings(config):
    embeddings = GoogleGenerativeAIEmbeddings(model = config.embeddings2)
    return embeddings

def read_yaml(path='../config/configuration.yaml'):
    assert Path(path).exists(),f"{path} doesn't exists"
    with open(path, 'r') as file:
        config = yaml.safe_load(file)
    return Namespace(**config)

config = read_yaml('config/configuration.yaml')
logger=start_logger(config).getLogger(__name__)
    