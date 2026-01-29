from patchright.async_api import expect, Page
from patchright._impl._errors import TimeoutError as PlayTimeoutError
from browser import Browser
from pathlib import Path
import pdfplumber
from io import BytesIO
from config import obter_dados_config
from logging_config import get_logger
import asyncio
from exceptions import *
from retry import ui_retry, bootstrap_retry


logger = get_logger(__name__)

class Webform:
    def __init__(self, page: Page, browser: Browser):
        self.page = page
        self.browser = browser
        self.config = obter_dados_config()
        self.cliente = None


    @classmethod
    async def create(cls, page, browser: Browser):
        if asyncio.iscoroutine(page):
            page = await page
        return cls(page, browser)
    

    @bootstrap_retry
    async def acessar_portal(self):
        url = self.config['url']
        try:
            await self.page.goto(url, wait_until='networkidle', timeout=60000)
            btn_login_certif = self.page.locator("a.img-certificado")
            await expect(btn_login_certif).to_be_visible()
        except Exception as e:
            logger.critical(f'Falha ao acessar o portal: {e}')
            raise ErroTecnico(e)


    @bootstrap_retry
    async def login(self):
        try:
            btn_login_certif = self.page.locator("a.img-certificado")
            await btn_login_certif.click()
            btn_nova_nfse = self.page.locator("a.btnAcesso[data-original-title='Nova NFS-e']")
            await expect(btn_nova_nfse).to_be_visible()        
            logger.info('Autenticação bem-sucedida')
        except PlayTimeoutError as e:
            logger.error(f'Portal instável: {e}')
            raise SystemTimeoutError(e)
        except Exception as e:
            logger.error(f'Falha inesperada na autenticação: {e}')
            raise ErroTecnico(e)


    async def logout(self):
        try:
            menu_perfil = self.page.locator("li.dropdown.perfil")
            await menu_perfil.click()
            await expect(menu_perfil).to_be_enabled()
            await self.page.get_by_role("link", name="Sair").click()
        except PlayTimeoutError:
            logger.warning("Timeout ao tentar realizar logout")
            raise SystemTimeoutError(e)
        except Exception as e:
            logger.error(f'Erro ao fazer logout: {e}')
            raise ErroTecnico(e)

    
    @ui_retry
    async def gerar_nova_nf(self, primeira=False):
        try:
            if primeira:
                btn_nova_nfse = self.page.locator("a.btnAcesso[data-original-title='Nova NFS-e']")
            else:
                btn_nova_nfse = self.page.locator("#btnNovaNFSe")
            await btn_nova_nfse.click()
        except PlayTimeoutError as e:
            logger.error(f'Timeout na geração da nova nota fiscal: {e}')
            logger.warning('Tentando regarregar a página [NOVA NFSE]...')
            raise SystemTimeoutError(e)
        except Exception as e:
            logger.error(f'Erro inesperado na geração da nova nota fiscal: {e}')
            raise ErroTecnico(e)

    
    @ui_retry
    async def preencher_tela_pessoas(self, data):
        try:
            logger.info(self.cliente.ResponsávelFinanceiro)
            logger.info(self.cliente.CPF)
            campo_data = self.page.locator("input.form-control.data")
            await expect(campo_data).to_be_editable()
            logger.info('Tela PESSOAS carregada')
            
            await campo_data.click()
            await campo_data.fill(data)
            await self.page.locator("body").click()

            localizacao_tomador = self.page.locator("//div[@id='pnlTomador']//label[contains(.,'Brasil')]/span")
            await expect(localizacao_tomador).to_be_enabled()
            await localizacao_tomador.click()
            
            cpf_tomador = self.page.locator('#Tomador_Inscricao')
            await cpf_tomador.fill(str(self.cliente.CPF))
            
            btn_pesquisa_cpf = self.page.locator("#btn_Tomador_Inscricao_pesquisar")
            await btn_pesquisa_cpf.click()

            await self.page.get_by_role("button", name="Avançar").click()
        except PlayTimeoutError as e:
            logger.error(f'Timeout na tela [PESSOAS]: {e}')
            logger.warning('Tentando regarregar a página [PESSOAS]...')
            raise SystemTimeoutError(e)
        except AssertionError as e:
            logger.error(f'Erro de asserção na tela [PESSOAS]: {e}')
            logger.warning('Tentando regarregar a página [PESSOAS]...')
            raise SystemAssertionError(e)
        except ErroNegocio:
            raise ErroNegocio('Erro na tela [PESSOAS]')
        except Exception as e:
            logger.error('Erro inesperado ao preencher a página [PESSOAS]')
            logger.error(e)
            raise ErroTecnico(e)

    
    @ui_retry
    async def preencher_tela_servicos(self, mes, ano):
        municipio = self.config['municipio']
        cod_trib_nac_completo = self.config['cod_trib_nac_completo']
        nbs_pre = self.config['nbs_pre']
        nbs_fund = self.config['nbs_fund']
        
        try:
            campo_municipio = self.page.locator("#pnlLocalPrestacao").get_by_label("")
            await expect(campo_municipio).to_be_enabled()
            logger.info('Tela SERVIÇOS carregada')
            await campo_municipio.click()

            pesquisa_municipio = self.page.get_by_role("searchbox", name="Search")
            await pesquisa_municipio.fill(municipio)

            await self.page.get_by_role("option", name=municipio).click()

            cod_trib_nac_prefix = cod_trib_nac_completo.split()[0].replace('.', '')

            await self.page.get_by_label("", exact=True).click()
            campo_busca_cod_trib_nac = self.page.get_by_role("searchbox", name="Search")
            await campo_busca_cod_trib_nac.fill(cod_trib_nac_prefix)
            await self.page.get_by_role("option", name=cod_trib_nac_completo).click()

            await self.page.locator("i").nth(1).click()
            texto_descricao = f'PRESTAÇÃO DE SERVIÇO EDUCAÇÃO INFANTIL/FUNDAMENTAL MÊS {mes}/{ano} - ALUNO {self.cliente.Aluno}'
            await self.page.locator("#ServicoPrestado_Descricao").fill(texto_descricao)

            campo_nbs = self.page.locator("#ServicoPrestado_CodigoNBS_chosen")
            await campo_nbs.click()

            nbs = nbs_pre if self.cliente.Acumulador == '1' else nbs_fund

            await campo_nbs.locator("input").press_sequentially(nbs.split(' ')[0], delay=50)
            await campo_nbs.locator("input").press("Enter")

            await self.page.get_by_role("button", name="Avançar").click()
        except PlayTimeoutError as e:
            logger.error(f'Timeout na tela [SERVIÇOS]: {e}')
            logger.warning('Tentando regarregar a página [SERVIÇOS]...')
            raise SystemTimeoutError(e)
        except AssertionError as e:
            logger.error(f'Erro de asserção na tela [SERVIÇOS]: {e}')
            logger.warning('Tentando regarregar a página [SERVIÇOS]...')
            raise SystemAssertionError(e)
        except ErroNegocio:
            raise ErroNegocio('Erro na tela [SERVIÇOS]')
        except Exception as e:
            logger.error('Erro inesperado ao preencher a tela [SERVIÇOS]')
            logger.error(e)
            raise ErroTecnico(e)

    
    @ui_retry
    async def prencher_tela_valores(self):
        situacao_trib = self.config['situacao_trib']
        aliq_pis = self.config['aliq_pis']
        aliq_cofins = self.config['aliq_cofins']
        trib_fed = self.config['trib_fed']
        trib_est = self.config['trib_est']
        trib_mun = self.config['trib_mun']
        
        try:
            logger.info(f'Valor: {self.cliente.ValorTotal}')
            campo_valor_servico = self.page.locator('#Valores_ValorServico')
            await expect(campo_valor_servico).to_be_editable()
            logger.info('Tela VALORES carregada')

            await campo_valor_servico.fill(str(self.cliente.ValorTotal))
            await self.page.locator("body").click()

            opcoes_trib_mun = await self.page.locator("#pnlOperacaoTributavel label:has-text('Não') span").all()
            elegib_issqn = opcoes_trib_mun[0]
            retenc_issqn = opcoes_trib_mun[1]
            beneficio_mun = opcoes_trib_mun[2]

            await elegib_issqn.click()
            await retenc_issqn.click()
            await beneficio_mun.click()

            campo_situacao_trib = self.page.locator('#TributacaoFederal_PISCofins_SituacaoTributaria_chosen')
            await campo_situacao_trib.click()
            await campo_situacao_trib.get_by_text(situacao_trib).click()

            check_n_retido = self.page.locator("label:has-text('Não Retido') span")
            await check_n_retido.click()

            base_calc = self.page.locator('#TributacaoFederal_PISCofins_BaseDeCalculo')
            await base_calc.fill(str(self.cliente.ValorTotal))

            campo_aliq_pis = self.page.locator('#TributacaoFederal_PISCofins_AliquotaPIS')
            await campo_aliq_pis.fill(aliq_pis)
            
            campo_aliq_cofins = self.page.locator('#TributacaoFederal_PISCofins_AliquotaCOFINS')
            await campo_aliq_cofins.fill(aliq_cofins)

            config_valores = self.page.locator("label:has-text('Configurar os valores percentuais correspondentes') span")
            await config_valores.click()

            percent_fed = self.page.locator("#ValorTributos_PercentualTotalFederal")
            await percent_fed.fill(trib_fed)
            
            percent_est = self.page.locator("#ValorTributos_PercentualTotalEstadual")
            await percent_est.fill(trib_est)
            
            percent_mun = self.page.locator("#ValorTributos_PercentualTotalMunicipal")
            await percent_mun.fill(trib_mun)

            await self.page.get_by_role("button", name="Avançar").click()
        except PlayTimeoutError as e:
            logger.error(f'Timeout na tela [VALORES]: {e}')
            logger.warning('Tentando regarregar a página [VALORES]...')
            raise SystemTimeoutError(e)
        except AssertionError as e:
            logger.error(f'Erro de asserção na tela [VALORES]: {e}')
            logger.warning('Tentando regarregar a página [VALORES]...')
            raise SystemAssertionError(e)
        except ErroNegocio:
            raise ErroNegocio('Erro na tela [VALORES]')
        except Exception as e:
            logger.error('Erro inesperado ao preencher a tela [VALORES]')
            logger.error(e)
            raise ErroTecnico(e)

    
    @ui_retry
    async def emitir_nota(self):
        try:
            emitir_nfse = self.page.locator("#btnProsseguir")
            expect(emitir_nfse).to_be_enabled()
            await emitir_nfse.click()
        except PlayTimeoutError as e:
            logger.error(f'Timeout na tela [EMITIR NFSE]: {e}')
            logger.warning('Tentando regarregar a página [EMITIR NFSE]')
            raise SystemTimeoutError(e)
        except Exception as e:
            logger.error(f'Erro inesperado na tela [EMITIR NFSE]: {e}')
            raise ErroTecnico(e)

    
    @ui_retry
    async def baixar_arquivos(self, formato):
        try:
            formatos = {
                'xml': self.page.locator("#btnDownloadXml"),
                'pdf': self.page.locator("#btnDownloadDANFSE")
            }
            
            btn_download = formatos.get(formato)
            await expect(btn_download).to_be_enabled(timeout=30000)

            async with self.page.expect_download() as download_info:
                await btn_download.click()

            download = await download_info.value
            return download
        except PlayTimeoutError as e:
            logger.error(f'Erro no download do arquivo: {e}')
            raise SystemTimeoutError(e)
        except Exception as e:
            logger.error(f'Erro inesperado no download do arquivo: {e}')
            raise ErroTecnico(e)

 
    async def salvar_xml(self, download_info, num_nfs):
        try:
            if not num_nfs:
                raise ErroNegocio('Número da NFS-e não encontrado')
            download_path = await download_info.path()
            original_path = Path(download_path)

            if not original_path.exists():
                raise ErroTecnico(f"Arquivo não encontrado: {original_path}")

            novo_path = original_path.parent / f"nfse_{num_nfs:0>4}.xml"
            original_path.rename(novo_path)
            logger.info(f"Arquivo NFSe (XML) salvo em: {novo_path}")
        except ErroNegocio as e:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao salvar o arquivo XML: {e}")
            raise ErroTecnico(e)

  
    async def processar_pdf(self, download_info):
        try:
            download_path = await download_info.path()
            pdf_bytes = Path(download_path).read_bytes()
            pdf_file = BytesIO(pdf_bytes)
            
            with pdfplumber.open(pdf_file) as pdf:
                textoBruto = ''
                for page in pdf.pages:
                    textoBruto += page.extract_text()
            
            linha_num_nfs = 6
            pos_num_nfs = 0
            linhas = textoBruto.splitlines()

            try:
                num_nfs = linhas[linha_num_nfs].split()[pos_num_nfs]
            except (IndexError, ValueError):
                raise ErroNegocio('Número da NFS-e não encontrado no PDF')

            logger.info(f"Número da NFS-e extraído do PDF: {num_nfs}")
            logger.info("Arquivo PDF temporário processado e deletado.")
            return num_nfs
        except ErroNegocio as e:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao processar o PDF: {e}")
            raise ErroTecnico(e)
        finally:
            if download_info and hasattr(download_info, 'delete'):
                await download_info.delete()
