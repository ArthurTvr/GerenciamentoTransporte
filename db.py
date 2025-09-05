
# db.py

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://ArthurTvr:Ardan147.@transportedb.ypeemf6.mongodb.net/?retryWrites=true&w=majority&appName=transportedb"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Conexão com MongoDB bem-sucedida!")
except Exception as e:
    print(e)

DB_NAME = "transporte_db"   # Nome do banco
COL_ATIVOS = "ativos"       # Nome da coleção de alunos ativos
COL_ESPERA = "espera"       # Nome da coleção de lista de espera


# -------------------------------
# CONEXÃO
# -------------------------------
def get_db():
    """
    Retorna a instância do banco MongoDB.
    """
    client = MongoClient(uri, server_api=ServerApi('1'))
    return client[DB_NAME]

def get_collection(nome):
    """
    Retorna a coleção informada pelo nome.
    """
    db = get_db()
    return db[nome]


# -------------------------------
# ATALHOS
# -------------------------------
def get_ativos_collection():
    """
    Retorna a coleção de alunos ativos.
    """
    return get_collection(COL_ATIVOS)


def get_espera_collection():
    """
    Retorna a coleção da lista de espera.
    """
    return get_collection(COL_ESPERA)
