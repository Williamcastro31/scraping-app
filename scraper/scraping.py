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


        def fechar_tutorial(pgn, locator):

            try:

                fechar_tutorial = pgn.locator(locator)
                
                fechar_tutorial.click()
                time.sleep(2)

            except Exception as e:

                return f"Erro ao fechar o tutorial: {e}"




        def encortrar_ean(pgn, cd_produto):

            # Pegar todos os links "Mais informações"
            links = pgn.locator("text=Mais informações")
            total = links.count()

            encontrado = False

            for i in range(total):
                # Recarregar os links (porque o DOM muda a cada clique/fechamento)
                links = page.locator("text=Mais informações")

                # Clicar no link i
                links.nth(i).click()

                time.sleep(2)

                # Esperar modal aparecer
                pgn.wait_for_selector('xpath=//*[@id="modal-mais-informacoes"]/div[2]')  

                # Pegar todo o texto do modal
                modal_texto = page.locator('xpath=//*[@id="modal-mais-informacoes"]/div[2]').inner_text()

                # Verificar se contém o EAN procurado
                if cd_produto in modal_texto:

                    encontrado = True
                    break  # parar o loop

                # Fechar modal
                page.locator('xpath=//*[@id="modal-mais-informacoes"]/div[1]/a').click()

                # Garantir que a tela voltou
                page.wait_for_selector("text=Mais informações")


        

        def transforma_dado(dado: dict) -> dict:
            """
            Transforma o dicionário original no formato desejado,
            tratando quando 'Adicional' não tiver valor.
            """
            # Regex para capturar "quantidade = + desconto"
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
                page.goto(f"https://trade.fidelize.com.br/msd/webol/index.php?r=site/login", timeout=15000)

                # aceitar cookies
                page.wait_for_load_state("load")   
                page.click('xpath=/html/body/div[4]/div[2]/div/div[1]/div/div[2]/div/button[2]')
                time.sleep(2)
   

                # login
                try:
                       
                    campo_user = 'xpath=//*[@id="LoginForm_username"]'
                    campo_senha = 'xpath=//*[@id="LoginForm_password"]'
                    bt_entrar = 'xpath=//*[@id="login-form"]/input[5]'

                    self.realizar_login(page, campo_senha, campo_user, bt_entrar)
    
                except Exception as e:

                    return {'erro_login': f"Erro ao localizar o campo de login ou senha: {e}"}

                # Fechar tela de tutorial pagina principal
                fechar_tutorial(page, 'xpath=/html/body/div[12]/div/div[5]/a')
        

                # Acessar o módulo de cotações
                page.wait_for_load_state("load")
                page.click('xpath=//*[@id="nav"]/li[1]/a/span')


                # Fechar tela de tutorial pagina cotações
                fechar_tutorial(page, 'xpath=/html/body/div[10]/div/div[5]/a')

                # Informar CNPJ
                page.wait_for_load_state("load")
                campo_cnpj = page.locator('xpath=//*[@id="clientes-grid"]/table/thead/tr[2]/td[4]/input')
                campo_cnpj.fill(self.cnpj)
                campo_cnpj.press("Enter")

                #Pesquisar o cliente
                # Se aparecer "Nenhum resultado encontrado" encerrar o naverador e retornar Cliente não encontrado para o cpnj informado
                time.sleep(2)

                dict_erro_cliente = {'codigoProduto': self.cd_produto, 'descricaoProduto':self.descricao ,
                                   'cnpjCliente': self.cnpj, 'integradorald': self.integradorald, 'desconto':'', 'descontoProgressivo':'', 'erro_cliente': f"Cliente não encontrado para o CNPJ informado. ({self.cnpj})"}


                nenhum_resultado_locator = page.locator('xpath=//*[@id="clientes-grid"]/table/tbody/tr/td/span')
                if nenhum_resultado_locator.count() > 0:
                    texto = nenhum_resultado_locator.first.inner_text()
                    if texto.strip() == "Nenhum resultado encontrado.":
                        browser.close()
                        return dict_erro_cliente
                else:
                    # Alternativa: verificar diretamente nos <td>
                    td_locators = page.locator('xpath=//*[@id="clientes-grid"]/table/tbody/tr/td')
                    for i in range(td_locators.count()):
                        if td_locators.nth(i).inner_text().strip() == "Nenhum resultado encontrado.":
                            browser.close()
                            return dict_erro_cliente

                # Clicar no cliente
                page.click('xpath=//*[@id="clientes-grid"]/table/tbody/tr/td[4]')

                time.sleep(2)

                # Clicar no nome produto da cotação
                
                # Procurar pela descrição do produto

                container = page.locator('xpath=//*[@id="body-tabelas-condicao"]/table/tbody')

                dict_erro_prod = {'codigoProduto': self.cd_produto, 'descricaoProduto':self.descricao ,
                                   'cnpjCliente': self.cnpj, 'integradorald': self.integradorald, 'desconto':'', 'descontoProgressivo':'', 'erro_produto': f"Produto '{self.descricao}' não encontrado no cadastro do cliente."}

                try:
                    elemento_produto = container.get_by_text(self.descricao, exact=False)
                    if elemento_produto.count() == 0:
                        browser.close()
                        return dict_erro_prod
                    elemento_produto.first.click()
                except Exception as e:
                    browser.close()

                    return dict_erro_prod

                #-----

                # Procurar pelo EAN
                #encortrar_ean(page, self.cd_produto)

                # Clicar em criar
                time.sleep(1)
                page.click('xpath=//*[@id="btn-submit"]')

                # Selecionar o CD
                time.sleep(1)
                page.click('xpath=//*[@id="distribuidores-disponiveis"]/li[1]/div[1]')

                # Clicar em avançar
                time.sleep(1)
                page.click('xpath=//*[@id="btn-salvar-distribuidores"]')
                time.sleep(3)
                page.wait_for_load_state("load")

                ##-------------------------------------##

                # Espera a tabela carregar
                page.wait_for_load_state("load")

                # Localiza a tabela
                tabela = page.locator('xpath=//*[@id="lista-produtos-tabela"]')

                # Todas as linhas do corpo
                linhas = tabela.locator("tbody tr")

                # Itera sobre as linhas
                qtd_linhas = linhas.count()
                for i in range(qtd_linhas):
                    celulas = linhas.nth(i).locator("td")
                    
                    produto = celulas.nth(2).inner_text()   # Coluna Produto
                    base = celulas.nth(4).inner_text()      # Coluna Base
                    adicional = celulas.nth(5).inner_text() # Coluna Adicional

                    dict_extracao = {
                        "Produto": produto.strip(),
                        "Base": base.strip(),
                        "Adicional": adicional.strip()
                    }


                dict_extracao_final = transforma_dado(dict_extracao)

                # Adicionar informações adicionais
                dict_extracao_final["codigoProduto"] = self.cd_produto
                dict_extracao_final["cnpjCliente"] = self.cnpj
                dict_extracao_final["integradorald"] = self.integradorald

                
                time.sleep(2)
                browser.close()

                return dict_extracao_final
            
        except Exception as e:

            return {'erro_scraping': f"Erro ao acessar o site: {e}"}
   
