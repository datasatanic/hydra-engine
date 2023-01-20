from whoosh.analysis import StemmingAnalyzer
import json
from nltk.stem.snowball import SnowballStemmer

en_stemmer = SnowballStemmer('english')
ru_stemmer = SnowballStemmer("russian")


def multilang_stemmer(word):
    word = en_stemmer.stem(word)
    word = ru_stemmer.stem(word)
    return word


multilang_analyzer = StemmingAnalyzer(stemfn=multilang_stemmer)
