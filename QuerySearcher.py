
from whoosh.fields import Schema, KEYWORD
from whoosh.index import create_in
from whoosh.qparser import QueryParser

from ixapipes.tok import IxaPipesTokenizer
from ixapipes.pos import IxaPipesPosTagger

from scrapper import get_lemmatized_text

import os.path

topics = ["Azken berriak", "Berri irakurrienak", "Gizartea", "Politika", "Ekonomia", "Mundua", "Iritzia"
            , "Kultura", "Kirola", "Bizigiro"]

articles = ["Akusatuek uste dute auzia «torturak pozoituta» dagoela hastapenetatik", "Euskara aktibatzeko praktikak",
"Bederatzi lagun hil dira Suedian, hegazkin istripu batean", "Agustin Ibarrolaren 'Gernika' erosi du Bilboko Arte Ederren Museoak"]

class QuerySearcher:

    def __init__(self, documents = []):
        '''
        Constructor of QuerySearcher object. If no documents are given, the list is filled
        with predefined values.

        Parameters:
            - documents (List): List of the documents to search
        '''
        if documents == []:
            self.documents = ["Azken berriak", "Berri irakurrienak", "Gizartea", "Politika", "Ekonomia", "Mundua", "Iritzia", "Kultura", "Kirola", "Bizigiro"]

        else:
            self.documents = documents

        self.dict_documents = {}
    

    def __lemmatize_query(self, query, tokenizer, lemmatizer):
        '''
        Lemmatizes the query given by the user

        Parameters:
            - query (String): Query given by the user
            - tokenizer (IxaPipesTokenizer): Tokenizer object
            - lemmatizer (IxaPipesPosTagger): Lemmatizer object

        Returns:
            String which contains the lemmatized user query 
        '''
        tokens = tokenizer._run_text(query)
        naf_text = lemmatizer._run_text(tokens)
        lemmatized_text = get_lemmatized_text(str(naf_text))
        return lemmatized_text

    def __lemmatize_documents(self, tokenizer, lemmatizer):
        '''
        Lemmatizes all the documents stored at self.documents attribute. self.dict_documents is filled 
        where: key = lemmatized document, value = original document

        Parameters:
            - tokenizer (IxaPipesTokenizer): Tokenizer object
            - lemmatizer (IxaPipesPosTagger): Lemmatizer object

        Returns:
            List with all the lemmatized documents 
        '''
        documents = []
        for document in self.documents:
            tokens = tokenizer._run_text(document)
            naf_text = lemmatizer._run_text(tokens)
            lemmatized_text = get_lemmatized_text(naf_text)
            documents.append(lemmatized_text)
            self.dict_documents[lemmatized_text] = document

        return documents

    def __initialize_tools(self):
        '''
        Initializes tokenizer and lemmatizer objects.

        Returns:
            - IxaPipesTokenizer: Tokenizer object for Basque language
            - IxaPipesPosTagger: Lemmatizer object for Basque language
        '''
        tokenizer = IxaPipesTokenizer('eu')
        lemmatizer = IxaPipesPosTagger('eu',
                                    'morph-models-1.5.0/eu/eu-pos-perceptron-epec.bin',
                                    'morph-models-1.5.0/eu/eu-lemma-perceptron-epec.bin')

        return tokenizer, lemmatizer

    
    def __initialize_documents_schema(self, documents):
        '''
        Initializes Whoosh schema with the lemmatized documents

        Parameters:
            - documents (List): List of all the lemmatized documents

        Returns:
            Whoosh writer object
        '''
        schema = Schema(document = KEYWORD(stored=True))
    
        if not os.path.exists("index"):
            os.mkdir("index")

        ix = create_in("index", schema)

        writer = ix.writer()

        for document in documents:
            writer.add_document(document = document)

        writer.commit()

        return ix

    def __search(self, query, documents):
        '''
        Given lemmatized query and documents, returns the closest lemmatized document to the user query

        Parameters:
            - query (String): Lemmatized user query
            - documents (List): List of the lemmatized documents

        Returns:
            String with the closest lemmatized document. In case no documents are found, None is returned
        '''
        ix = self.__initialize_documents_schema(documents)

        with ix.searcher() as searcher:
            parser = QueryParser("document", ix.schema)
            myquery = parser.parse(query)

            results = searcher.search(myquery)

            if not results:
                return None

            else:
                return results[0].get('document')


    def search_query(self, query):
        '''
        Searches the closest document of self.documents attribute to the user query. In case no 
        document is found, Exception is raised.

        Parameters:
            - query (String): User query

        Returns:
            Closest document to the user query, if found
        '''
        print("Received query: " + str(query))
        tokenizer, lemmatizer = self.__initialize_tools()
        lemmatized_query = self.__lemmatize_query(query, tokenizer, lemmatizer)
        lemmatized_documents = self.__lemmatize_documents(tokenizer, lemmatizer)

        print("lemmatized_query "+ lemmatized_query)
        print("lemmatized documents " + str(lemmatized_documents))

        result = self.__search(lemmatized_query, lemmatized_documents)

        print(result)

        if result == None:
            raise Exception()

        tokenizer.close()
        lemmatizer.close()

        result = self.dict_documents.get(result)

        return result





if __name__ == "__main__":
    while True:
        query = str(input("Sartu zure galdera: "))
        qSearcher = QuerySearcher()
        result = qSearcher.search_query(query)
        print(result)
        


