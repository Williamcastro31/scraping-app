from fastapi import FastAPI
from scraper import scraping

app = FastAPI()
@app.get("/start_scraping")
def start_scraping(login: str, senha: str, cd_produto: str, descricao: str, cnpj: str, integradorald: str):

    login = login
    senha = senha
    cd_produto = cd_produto
    descricao = descricao
    cnpj = cnpj
    integradorald = integradorald

    get_buscar = scraping.Scraping_Cotacao(login, senha, cd_produto, descricao, cnpj, integradorald).trade_fidelize()
    get_buscar

    return get_buscar

#Chamar função para teste
#start_scraping("elfa1", "Mudar@2024", "7897572020115", "KEYTRUDA", "00382069000127", "8383393")