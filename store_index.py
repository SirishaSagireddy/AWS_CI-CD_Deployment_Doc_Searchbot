# Standard libraries
import os
from pathlib import Path
# Third-party libraries
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.vectorstores import Pinecone, Chroma
import pinecone
import chromadb
# Custom libraries
from src.helper import (
    load_data,
    text_split
    )
from src.prompt import prompt_template


class Store_to_db:
    def __init__(self, config):
        load_dotenv()
        model = config.model
        self.config = config
        self.docsearch = None
        if model == 'llama2':   
            from src.helper import download_hugging_face_embeddings
            from langchain.llms import CTransformers
            self.embeddings = download_hugging_face_embeddings(config)
            self.llm = CTransformers(
                model=config.model1_path,
                model_type="llama",
                config={'max_new_tokens':config.max_new_tokens,
                        'temperature':config.temperature})
        else:
            from src.helper import download_google_embeddings
            from langchain_google_genai import ChatGoogleGenerativeAI
            self.embeddings = download_google_embeddings(config)
            self.llm = ChatGoogleGenerativeAI(model=config.model2_path,
                                              temperature=config.temperature)
        PROMPT = PromptTemplate(template=prompt_template,
                                input_variables=["context", 
                                                 "question"])
        self.chain_type_kwargs = {"prompt": PROMPT}

    def create_qa_instance(self, url=None, file_path=None):

        if file_path:
            data_dir = self.config.data_dir
        elif url:
            print('elif_url****')
            data_dir = [url]
            print('data_dir:**', data_dir)
        
        vector_database = self.config.vector_database
        extracted_data = load_data(data_dir)
        print('extracted_data_store_index: ', extracted_data)
        text_chunks = text_split(extracted_data,
                                  self.config)
        def _create_pineconeindex():
            if self.config.model == 'llama2':
                pinecone.create_index(name=self.config.index_name,
                                      dimension=self.config.index_dim1,
                                      metric=self.config.index_metric)
            else:
                pinecone.create_index(name=self.config.index_name,
                                      dimension=self.config.index_dim2,
                                      metric=self.config.index_metric)
            assert pinecone.list_indexes(), 'pinecone index not created'
        
        def _create_chromadb_collection():
            Path(self.config.chroma_db_dir).mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(
                path=self.config.chroma_db_dir
                )
            collections = client.list_collections()
            if collections:
                client.delete_collection(self.config.default_chroma)
            vectordb = Chroma.from_documents(
                 documents=text_chunks,
                 embedding=self.embeddings,
                 persist_directory=self.config.chroma_db_dir,
                 )
            return vectordb
        if vector_database == 'pinecone':
            PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
            PINECONE_API_ENV = os.getenv("PINECONE_API_ENV")
            pinecone.init(api_key=PINECONE_API_KEY,
                          environment=PINECONE_API_ENV)
            if self.config.index_name in pinecone.list_indexes():
                # docsearch=Pinecone.from_existing_index(self.config.index_name, embeddings)
                pinecone.delete_index(self.config.index_name)
                _create_pineconeindex()
            else:
                _create_pineconeindex()
            
            try:
                self.docsearch = Pinecone.from_texts([t.page_content for t in text_chunks],
                                                    self.embeddings, index_name=self.config.index_name)
                # logger.info('Uploaded text chunks embeddings')
            except Exception as e:
                # logger.error('Error uploading text chunks embeddings: %s' % str(e))
                return "Failed to upload text chunks embeddings"
            
            # self.docsearch = Pinecone.from_texts(
            #     [t.page_content for t in text_chunks],
            #     self.embeddings, index_name=self.config.index_name)
        else:
            self.docsearch =  _create_chromadb_collection()
        qa = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.docsearch.as_retriever(search_kwargs={'k': self.config.k}),
            return_source_documents=True,
            chain_type_kwargs=self.chain_type_kwargs)
        self.qa = qa
        return "Completed"

if __name__ == '__main__':
    Store_to_db().create_qa_instance()