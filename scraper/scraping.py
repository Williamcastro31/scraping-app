from playwright.sync_api import sync_playwright
import re
import time


## Classe proncipal do projeto
class Scraping_Cotacao:

    def __init__(self, login: str, senha: str, cd_produto: str, descricao: str, cnpj: str, integradorald: str):

        self.login = login
        self.senha = senha
        self.cd_produto = cd_produto
        self.descricao = descricao
        self.cnpj = cnpj
        self.integradorald = integradorald


    def realizar_login(self, pgn, cp_senha, campo_login, bt_entrar, ):

        try:

            # Aguardar o carregamento completo da página
            pgn.wait_for_load_state("load")
            
            #Digitar a senha
            digitar_login = pgn.locator(campo_login)
            digitar_login.fill(self.login)

            #Digitar a senha
            digitar_senha = pgn.locator(cp_senha)
            digitar_senha.fill(self.senha)

            #Clicar no botão entrar
            clicar_entrar = pgn.locator(bt_entrar)
            clicar_entrar.click()

            time.sleep(2)

        
        except Exception as e:

            return


    def trade_fidelize(self):

        def fechar_tutorial(page, locator: str):
            """Tenta fechar tutoriais que aparecem em modal."""
            time.sleep(1)
            try:
                btn = page.locator(locator)
                if btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(1000)
            except Exception as e:
                return f"Erro ao fechar tutorial: {e}"

        def transforma_dado(dado: dict) -> dict:
            """
            Transforma o dicionário original no formato desejado,
            tratando quando 'Adicional' não tiver valor.
            """
            pattern = r"(\d+)\s+unidades\s*=\s*\+\s*([\d.,]+%)"
            desconto_progressivo = []

            if dado.get("Adicional"):  # só entra se tiver texto
                for qtd, desc in re.findall(pattern, dado["Adicional"]):
                    desconto_progressivo.append({
                        "quantidade": int(qtd),
                        "desconto": desc
                    })

            return {
                "descricaoProduto": dado.get("Produto", ""),
                "desconto": dado.get("Base", ""),
                "descontoProgressivo": desconto_progressivo
            }

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    # Acessar a página de login
                    page.goto("https://trade.fidelize.com.br/msd/webol/index.php?r=site/login", timeout=20000)
                    page.wait_for_load_state("load")

                    # Aceitar cookies se aparecer
                    try:
                        page.click('xpath=/html/body/div[4]/div[2]/div/div[1]/div/div[2]/div/button[2]', timeout=3000)
                    except:
                        pass

                    # Login
                    campo_user = 'xpath=//*[@id="LoginForm_username"]'
                    campo_senha = 'xpath=//*[@id="LoginForm_password"]'
                    bt_entrar = 'xpath=//*[@id="login-form"]/input[5]'
                    self.realizar_login(page, campo_senha, campo_user, bt_entrar)

                    # Fechar tutoriais
                    fechar_tutorial(page, 'xpath=/html/body/div[12]/div/div[5]/a')

                    # Acessar módulo de cotações
                    page.wait_for_selector('xpath=//*[@id="nav"]/li[1]/a/span')
                    page.click('xpath=//*[@id="nav"]/li[1]/a/span')
                    fechar_tutorial(page, 'xpath=/html/body/div[10]/div/div[5]/a')

                    # Informar CNPJ
                    campo_cnpj = page.locator('xpath=//*[@id="clientes-grid"]/table/thead/tr[2]/td[4]/input')
                    campo_cnpj.fill(self.cnpj)
                    campo_cnpj.press("Enter")
                    page.wait_for_timeout(2000)

                    dict_erro_cliente = {
                        'codigoProduto': self.cd_produto,
                        'descricaoProduto': self.descricao,
                        'cnpjCliente': self.cnpj,
                        'integradorald': self.integradorald,
                        'desconto': '',
                        'descontoProgressivo': '',
                        'erro_cliente': f"Cliente não encontrado para o CNPJ informado. ({self.cnpj})"
                    }
                    #time.sleep(2)
                    page.wait_for_load_state("load")            
                    # Validar cliente
                    nenhum_resultado = page.locator('xpath=//*[@id="clientes-grid"]/table/tbody/tr/td/span')
                    if nenhum_resultado.count() > 0 and "Nenhum resultado" in nenhum_resultado.first.inner_text():
                        return dict_erro_cliente

                    # Clicar no cliente
                    page.click('xpath=//*[@id="clientes-grid"]/table/tbody/tr/td[4]')
                    page.wait_for_timeout(1500)

                    # Procurar pela descrição do produto
                    container = page.locator('xpath=//*[@id="body-tabelas-condicao"]/table/tbody')
                    dict_erro_prod = {
                        'codigoProduto': self.cd_produto,
                        'descricaoProduto': self.descricao,
                        'cnpjCliente': self.cnpj,
                        'integradorald': self.integradorald,
                        'desconto': '',
                        'descontoProgressivo': '',
                        'erro_produto': f"Produto '{self.descricao}' não encontrado no cadastro do cliente."
                    }

                    
                    elemento_produto = container.get_by_text(self.descricao, exact=False)
                    page.wait_for_load_state("load") 
                    if elemento_produto.count() == 0:
                        return dict_erro_prod
                    elemento_produto.first.click()

                    # Clicar em criar cotação
                    page.wait_for_selector('xpath=//*[@id="btn-submit"]')
                    page.click('xpath=//*[@id="btn-submit"]')

                    # Selecionar CD e avançar
                    page.wait_for_selector('xpath=//*[@id="distribuidores-disponiveis"]/li[1]/div[1]')
                    page.click('xpath=//*[@id="distribuidores-disponiveis"]/li[1]/div[1]')
                    page.click('xpath=//*[@id="btn-salvar-distribuidores"]')
                    page.wait_for_load_state("load")

                    # Ler tabela de descontos
                    tabela = page.locator('xpath=//*[@id="lista-produtos-tabela"]')
                    linhas = tabela.locator("tbody tr")

                    if linhas.count() == 0:
                        return dict_erro_prod

                    # Só o primeiro produto (já que você clicou em 1)
                    celulas = linhas.nth(0).locator("td")
                    dict_extracao = {
                        "Produto": celulas.nth(2).inner_text().strip(),
                        "Base": celulas.nth(4).inner_text().strip(),
                        "Adicional": celulas.nth(5).inner_text().strip()
                    }

                    dict_extracao_final = transforma_dado(dict_extracao)
                    dict_extracao_final["codigoProduto"] = self.cd_produto
                    dict_extracao_final["cnpjCliente"] = self.cnpj
                    dict_extracao_final["integradorald"] = self.integradorald

                    return dict_extracao_final

                except Exception as e:
                    return {'erro_scraping': f"Erro no fluxo principal: {e}"}

                finally:
                    browser.close()

        except Exception as e:
            return {'erro_scraping': f"Erro ao iniciar Playwright: {e}"}

