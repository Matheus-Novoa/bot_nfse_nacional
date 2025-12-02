from patchright.sync_api import expect, Page
from patchright._impl._errors import TimeoutError as terror
from adapters import BrowserAdapter
from pathlib import Path
import pdfplumber
from io import BytesIO
from functools import wraps
from tenacity import retry, wait_fixed, retry_if_exception_type, stop_after_attempt
from config import obter_dados_config


def retentativa(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        dec = retry(
            retry=retry_if_exception_type((terror, AssertionError)),
            wait=wait_fixed(3),
            stop=stop_after_attempt(3),
            retry_error_callback=lambda rs: self.acao_apos_falha_total(rs)
        )
        bound = func.__get__(self, type(self))
        return dec(bound)(*args, **kwargs)
    return wrapper


class Webform:
    def __init__(self, page: Page, browser: BrowserAdapter):
        self.page = page
        self.browser = browser
        self.config = obter_dados_config()
        self.cliente = None


    def acao_apos_falha_total(self, retry_state):
        """
        Função a ser chamada quando todas as tentativas falharem.
        """
        print("="*50)
        print("ERRO CRÍTICO: Não foi possível preencher a tela de valores após múltiplas tentativas.")
        
        ultima_excecao = retry_state.outcome.exception()
        print(f"Última exceção capturada: {ultima_excecao}")
        print(f"Total de tentativas: {retry_state.attempt_number}")
        
        print("Fechando o sistema devido a erro persistente...")
        try:
            self.logout()
        finally:
            self.browser.close_browser()

    
    def acessar_portal(self):
        url = self.config['url']
        try:
            self.page.goto(url, wait_until='networkidle', timeout=60000)
            btn_login_certif = self.page.locator("a.img-certificado")
            expect(btn_login_certif).to_be_visible()
        except Exception as e:
            print(f'Falha ao acessar o portal: {e}')
            self.browser.close_browser()

 
    def login(self):
        try:
            btn_login_certif = self.page.locator("a.img-certificado")
            btn_login_certif.click()
            btn_nova_nfse = self.page.locator("a.btnAcesso[data-original-title='Nova NFS-e']")
            expect(btn_nova_nfse).to_be_visible()        
            print('Autenticação bem-sucedida')
        except Exception as e:
            print(f'Falha na autenticação: {e}')
            print('Tentando regarregar a página...')
            try:
                self.page.reload()
                expect(btn_login_certif).to_be_visible()
                print('Página recarregada')
            except:
                print('Falha no recarregamento da página')
                self.browser.close_browser()


    def logout(self):
        menu_perfil = self.page.locator("li.dropdown.perfil")
        menu_perfil.click()
        expect(menu_perfil).to_be_visible()
        self.page.get_by_role("link", name="Sair").click()

    
    @retentativa
    def gerar_nova_nf(self, primeira=False):
        try:
            if primeira:
                btn_nova_nfse = self.page.locator("a.btnAcesso[data-original-title='Nova NFS-e']")
            else:
                btn_nova_nfse = self.page.locator("#btnNovaNFSe")
            btn_nova_nfse.click()
        except Exception as e:
            print(f'Erro na geração da nova nota fiscal: {e}')

    
    @retentativa
    def preencher_tela_pessoas(self):
        data = self.config['data']
        
        try:
            print(self.cliente.ResponsávelFinanceiro)
            print(self.cliente.CPF)
            campo_data = self.page.locator("input.form-control.data")
            expect(campo_data).to_be_editable()
            print('Tela PESSOAS carregada')
            
            campo_data.click()
            campo_data.fill(data)
            self.page.locator("body").click()

            localizacao_tomador = self.page.locator("//div[@id='pnlTomador']//label[contains(.,'Brasil')]/span")
            expect(localizacao_tomador).to_be_enabled()
            localizacao_tomador.click()
            
            cpf_tomador = self.page.locator('#Tomador_Inscricao')
            cpf_tomador.fill(str(self.cliente.CPF))
            
            btn_pesquisa_cpf = self.page.locator("#btn_Tomador_Inscricao_pesquisar")
            btn_pesquisa_cpf.click()

            self.page.get_by_role("button", name="Avançar").click()
        except terror as e:
            print(f'SystemError: {e}')
            print('Tentando regarregar a página...')
            self.page.reload()
            raise

    
    @retentativa
    def preencher_tela_servicos(self, mes, ano):
        municipio = self.config['municipio']
        cod_trib_nac_completo = self.config['cod_trib_nac_completo']
        nbs_pre = self.config['nbs_pre']
        nbs_fund = self.config['nbs_fund']
        
        try:
            campo_municipio = self.page.locator("#pnlLocalPrestacao").get_by_label("")
            expect(campo_municipio).to_be_enabled()
            print('Tela SERVIÇOS carregada')
            campo_municipio.click()

            pesquisa_municipio = self.page.get_by_role("searchbox", name="Search")
            pesquisa_municipio.fill(municipio)

            self.page.get_by_role("option", name=municipio).click()

            cod_trib_nac_prefix = cod_trib_nac_completo.split()[0].replace('.', '')

            self.page.get_by_label("", exact=True).click()
            campo_busca_cod_trib_nac = self.page.get_by_role("searchbox", name="Search")
            campo_busca_cod_trib_nac.fill(cod_trib_nac_prefix)
            self.page.get_by_role("option", name=cod_trib_nac_completo).click()

            self.page.locator("i").nth(1).click()
            texto_descricao = f'PRESTAÇÃO DE SERVIÇO EDUCAÇÃO INFANTIL/FUNDAMENTAL MÊS {mes}/{ano} - ALUNO {self.cliente.Aluno}'
            self.page.locator("#ServicoPrestado_Descricao").fill(texto_descricao)

            campo_nbs = self.page.locator("#ServicoPrestado_CodigoNBS_chosen")
            campo_nbs.click()

            nbs = nbs_pre if self.cliente.Acumulador == '1' else nbs_fund

            campo_nbs.locator("input").press_sequentially(nbs.split(' ')[0], delay=50)
            campo_nbs.locator("input").press("Enter")

            self.page.get_by_role("button", name="Avançar").click()
        except terror as e:
            print(f'SystemError: {e}')
            print('Tentando regarregar a página...')
            self.page.reload()
            raise

    
    @retentativa
    def prencher_tela_valores(self):
        situacao_trib = self.config['situacao_trib']
        aliq_pis = self.config['aliq_pis']
        aliq_cofins = self.config['aliq_cofins']
        trib_fed = self.config['trib_fed']
        trib_est = self.config['trib_est']
        trib_mun = self.config['trib_mun']
        
        try:
            print(f'Valor: {self.cliente.ValorTotal}')
            campo_valor_servico = self.page.locator('#Valores_ValorServico')
            expect(campo_valor_servico).to_be_editable()
            print('Tela VALORES carregada')

            campo_valor_servico.fill(str(self.cliente.ValorTotal))
            self.page.locator("body").click()

            opcoes_trib_mun = self.page.locator("#pnlOperacaoTributavel label:has-text('Não') span").all()
            elegib_issqn = opcoes_trib_mun[0]
            retenc_issqn = opcoes_trib_mun[1]
            beneficio_mun = opcoes_trib_mun[2]

            elegib_issqn.click()
            retenc_issqn.click()
            beneficio_mun.click()

            campo_situacao_trib = self.page.locator('#TributacaoFederal_PISCofins_SituacaoTributaria_chosen')
            campo_situacao_trib.click()
            campo_situacao_trib.get_by_text(situacao_trib).click()

            check_n_retido = self.page.locator("label:has-text('Não Retido') span")
            check_n_retido.click()

            base_calc = self.page.locator('#TributacaoFederal_PISCofins_BaseDeCalculo')
            base_calc.fill(str(self.cliente.ValorTotal))

            campo_aliq_pis = self.page.locator('#TributacaoFederal_PISCofins_AliquotaPIS')
            campo_aliq_pis.fill(aliq_pis)
            
            campo_aliq_cofins = self.page.locator('#TributacaoFederal_PISCofins_AliquotaCOFINS')
            campo_aliq_cofins.fill(aliq_cofins)

            config_valores = self.page.locator("label:has-text('Configurar os valores percentuais correspondentes') span")
            config_valores.click()

            percent_fed = self.page.locator("#ValorTributos_PercentualTotalFederal")
            percent_fed.fill(trib_fed)
            
            percent_est = self.page.locator("#ValorTributos_PercentualTotalEstadual")
            percent_est.fill(trib_est)
            
            percent_mun = self.page.locator("#ValorTributos_PercentualTotalMunicipal")
            percent_mun.fill(trib_mun)

            self.page.get_by_role("button", name="Avançar").click()
        except terror as e:
            print(f'SystemError: {e}')
            print('Tentando regarregar a página...')
            self.page.reload()
            raise

    
    @retentativa
    def emitir_nota(self):
        emitir_nfse = self.page.locator("#btnProsseguir")
        emitir_nfse.click()

    
    @retentativa
    def baixar_arquivos(self, formato):
        formatos = {
            'xml': self.page.locator("#btnDownloadXml"),
            'pdf': self.page.locator("#btnDownloadDANFSE")
        }
        
        btn_download = formatos.get(formato)
        expect(btn_download).to_be_enabled(timeout=30000)

        with self.page.expect_download() as download_info:
            btn_download.click()

        return download_info
    
 
    def salvar_xml(self, download_info):
        download_xml = download_info.value
        original_path = Path(download_xml.path())

        novo_path = original_path.parent / f"nfse_{str(self.cliente.CPF).replace('.', '').replace('-', '')}_{self.cliente.Index}.xml"
        original_path.rename(novo_path)
        print(f"Arquivo NFSe (XML) salvo em: {novo_path}")

  
    def processar_pdf(self, download_info):
        download_pdf = download_info.value
        try:
            pdf_bytes = Path(download_pdf.path()).read_bytes()
            pdf_file = BytesIO(pdf_bytes)
            
            with pdfplumber.open(pdf_file) as pdf:
                textoBruto = ''
                for page in pdf.pages:
                    textoBruto += page.extract_text()
            
            linha_num_nfs = 6
            pos_num_nfs = 0
            num_nfs = textoBruto.splitlines()[linha_num_nfs].split()[pos_num_nfs]
            print(f"Número da NFS-e extraído do PDF: {num_nfs}")
        finally:
            download_pdf.delete()
            print("Arquivo PDF temporário processado e deletado.")
            return num_nfs
