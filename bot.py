from patchright.sync_api import expect, Page
from patchright._impl._errors import TimeoutError as terror
from datetime import datetime
from pathlib import Path
from io import BytesIO
import pdfplumber
from adpters import BrowserAdapter
from tenacity import retry, wait_fixed, retry_if_exception_type, stop_after_attempt
from dados import Dados


url = 'https://www.nfse.gov.br/EmissorNacional/Login'

data = '29/11/2025'
data_obj = datetime.strptime(data, '%d/%m/%Y')
meses = {
    '1': "Janeiro",
    '2': "Fevereiro",
    '3': "Março",
    '4': "Abril",
    '5': "Maio",
    '6': "Junho",
    '7': "Julho",
    '8': "Agosto",
    '9': "Setembro",
    '10': "Outubro",
    '11': "Novembro",
    '12': "Dezembro"
    }
mes = meses[str(data_obj.month)]
ano = str(data_obj.year)

municipio = 'Porto Alegre/RS'
cod_trib_nac_completo = '08.01.01 - Ensino regular pré-escolar, fundamental e médio'
nbs_pre = '122011200 - Serviços de pré-escola'
nbs_fund = '122012000 - Serviços de ensino fundamental'
situacao_trib = 'Operação Tributável com Alíquota Básica'
aliq_pis = '1,65'
aliq_cofins = '7,6'
trib_fed = '9,25'
trib_est = '0,00'
trib_mun = '4,00'
planilha_dados = r"C:\Users\novoa\OneDrive\Área de Trabalho\notas_MB\planilhas\zona_sul\escola_canadenseZS_nov25\Numeração de Boletos_Zona Sul_2025_NOVEMBRO.xlsx" 

dados_obj = Dados(
    arqPlanilha=planilha_dados,
    sede='Zona Sul'
)
df_afazer = dados_obj.obter_dados().copy()
df_afazer['Notas'] = df_afazer['Notas'].astype(str)


def acao_apos_falha_total(retry_state):
    """
    Função a ser chamada quando todas as tentativas de 'prencher_tela_valores' falharem.
    """
    print("="*50)
    print("ERRO CRÍTICO: Não foi possível preencher a tela de valores após múltiplas tentativas.")
    
    ultima_excecao = retry_state.outcome.exception()
    print(f"Última exceção capturada: {ultima_excecao}")
    print(f"Total de tentativas: {retry_state.attempt_number}")
    
    print("Fechando o sistema devido a erro persistente...")
    try:
        logout(page)
    finally:
        browser.close_browser()


retry_on_error = retry(
    retry=retry_if_exception_type((terror, AssertionError)),
    wait=wait_fixed(3),
    stop=stop_after_attempt(3),
    retry_error_callback=acao_apos_falha_total
)


def acessar_portal(page: Page, browser):
    try:
        page.goto(url, wait_until='networkidle', timeout=60000)
        btn_login_certif = page.locator("a.img-certificado")
        expect(btn_login_certif).to_be_visible()
    except Exception as e:
        print(f'Falha ao acessar o portal: {e}')
        browser.close_browser()


def login(page: Page, browser):
    try:
        btn_login_certif = page.locator("a.img-certificado")
        btn_login_certif.click()
        btn_nova_nfse = page.locator("a.btnAcesso[data-original-title='Nova NFS-e']")
        expect(btn_nova_nfse).to_be_visible()        
        print('Autenticação bem-sucedida')
    except Exception as e:
        print(f'Falha na autenticação: {e}')
        print('Tentando regarregar a página...')
        try:
            page.reload()
            expect(btn_login_certif).to_be_visible()
            print('Página recarregada')
        except:
            print('Falha no recarregamento da página')
            browser.close_browser()


def logout(page: Page):
    menu_perfil = page.locator("li.dropdown.perfil")
    menu_perfil.click()
    expect(menu_perfil).to_be_visible()
    page.get_by_role("link", name="Sair").click()


def gerar_nova_nf(page: Page, primeira=False):
    try:
        if primeira:
            btn_nova_nfse = page.locator("a.btnAcesso[data-original-title='Nova NFS-e']")
        else:
            btn_nova_nfse = page.locator("#btnNovaNFSe")
        
        btn_nova_nfse.click()
    except Exception as e:
        print(f'Erro na geração da nova nota fiscal: {e}')


@retry_on_error
def preencher_tela_pessoas(cliente, page: Page):
    try:
        print(cliente.ResponsávelFinanceiro)
        print(cliente.CPF)
        campo_data = page.locator("input.form-control.data")
        expect(campo_data).to_be_editable()
        print('Tela PESSOAS carregada')
        
        campo_data.click()
        campo_data.fill(data)
        page.locator("body").click()

        localizacao_tomador = page.locator("//div[@id='pnlTomador']//label[contains(.,'Brasil')]/span")
        expect(localizacao_tomador).to_be_enabled()
        localizacao_tomador.click()
        
        cpf_tomador = page.locator('#Tomador_Inscricao')
        cpf_tomador.fill(str(cliente.CPF))
        
        btn_pesquisa_cpf = page.locator("#btn_Tomador_Inscricao_pesquisar")
        btn_pesquisa_cpf.click()

        page.get_by_role("button", name="Avançar").click()
    except terror as e:
        print(f'SystemError: {e}')
        print('Tentando regarregar a página...')
        page.reload()
        raise


@retry_on_error
def preencher_tela_servicos(cliente, page: Page):
    try:
        campo_municipio = page.locator("#pnlLocalPrestacao").get_by_label("")
        expect(campo_municipio).to_be_enabled()
        print('Tela SERVIÇOS carregada')
        campo_municipio.click()

        pesquisa_municipio = page.get_by_role("searchbox", name="Search")
        pesquisa_municipio.fill(municipio)

        page.get_by_role("option", name=municipio).click()

        cod_trib_nac_prefix = cod_trib_nac_completo.split()[0].replace('.', '')

        page.get_by_label("", exact=True).click()
        campo_busca_cod_trib_nac = page.get_by_role("searchbox", name="Search")
        campo_busca_cod_trib_nac.fill(cod_trib_nac_prefix)
        page.get_by_role("option", name=cod_trib_nac_completo).click()

        page.locator("i").nth(1).click()
        texto_descricao = f'PRESTAÇÃO DE SERVIÇO EDUCAÇÃO INFANTIL/FUNDAMENTAL MÊS {mes}/{ano} - ALUNO {cliente.Aluno}'
        page.locator("#ServicoPrestado_Descricao").fill(texto_descricao)

        campo_nbs = page.locator("#ServicoPrestado_CodigoNBS_chosen")
        campo_nbs.click()

        nbs = nbs_pre if cliente.Acumulador == '1' else nbs_fund

        campo_nbs.locator("input").press_sequentially(nbs.split(' ')[0], delay=50)
        campo_nbs.locator("input").press("Enter")

        page.get_by_role("button", name="Avançar").click()
    except terror as e:
        print(f'SystemError: {e}')
        print('Tentando regarregar a página...')
        page.reload()
        raise


@retry_on_error
def prencher_tela_valores(cliente, page: Page):
    try:
        print(f'Valor: {cliente.ValorTotal}')
        campo_valor_servico = page.locator('#Valores_ValorServico')
        expect(campo_valor_servico).to_be_editable()
        print('Tela VALORES carregada')

        campo_valor_servico.fill(str(cliente.ValorTotal))
        page.locator("body").click()

        opcoes_trib_mun = page.locator("#pnlOperacaoTributavel label:has-text('Não') span").all()
        elegib_issqn = opcoes_trib_mun[0]
        retenc_issqn = opcoes_trib_mun[1]
        beneficio_mun = opcoes_trib_mun[2]

        elegib_issqn.click()
        retenc_issqn.click()
        beneficio_mun.click()

        campo_situacao_trib = page.locator('#TributacaoFederal_PISCofins_SituacaoTributaria_chosen')
        campo_situacao_trib.click()
        campo_situacao_trib.get_by_text(situacao_trib).click()

        check_n_retido = page.locator("label:has-text('Não Retido') span")
        check_n_retido.click()

        base_calc = page.locator('#TributacaoFederal_PISCofins_BaseDeCalculo')
        base_calc.fill(str(cliente.ValorTotal))

        campo_aliq_pis = page.locator('#TributacaoFederal_PISCofins_AliquotaPIS')
        campo_aliq_pis.fill(aliq_pis)
        
        campo_aliq_cofins = page.locator('#TributacaoFederal_PISCofins_AliquotaCOFINS')
        campo_aliq_cofins.fill(aliq_cofins)

        config_valores = page.locator("label:has-text('Configurar os valores percentuais correspondentes') span")
        config_valores.click()

        percent_fed = page.locator("#ValorTributos_PercentualTotalFederal")
        percent_fed.fill(trib_fed)
        
        percent_est = page.locator("#ValorTributos_PercentualTotalEstadual")
        percent_est.fill(trib_est)
        
        percent_mun = page.locator("#ValorTributos_PercentualTotalMunicipal")
        percent_mun.fill(trib_mun)

        page.get_by_role("button", name="Avançar").click()
    except terror as e:
        print(f'SystemError: {e}')
        print('Tentando regarregar a página...')
        page.reload()
        raise


@retry_on_error
def emitir_nota(page: Page):
    emitir_nfse = page.locator("#btnProsseguir")
    emitir_nfse.click()


@retry_on_error
def baixar_arquivos(formato, page: Page):
    formatos = {
        'xml': page.locator("#btnDownloadXml"),
        'pdf': page.locator("#btnDownloadDANFSE")
    }
    
    btn_download = formatos.get(formato)
    expect(btn_download).to_be_enabled(timeout=30000)

    with page.expect_download() as download_info:
        btn_download.click()

    return download_info


def salvar_xml(download_info, cliente):
    download_xml = download_info.value
    original_path = Path(download_xml.path())

    novo_path = original_path.parent / f"nfse_{str(cliente.CPF).replace('.', '').replace('-', '')}_{cliente.Index}.xml"
    original_path.rename(novo_path)
    print(f"Arquivo NFSe (XML) salvo em: {novo_path}")


def processar_pdf(download_info):
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


browser = BrowserAdapter()
page = browser.setup_browser()

acessar_portal(page, browser)
login(page, browser)
gerar_nova_nf(page, primeira=True)

for cliente in df_afazer.itertuples():
    preencher_tela_pessoas(cliente, page)
    preencher_tela_servicos(cliente, page)
    prencher_tela_valores(cliente, page)
    emitir_nota(page)
    
    download_info_xml = baixar_arquivos('xml', page)
    if download_info_xml:
        salvar_xml(download_info_xml, cliente)

    download_info_pdf = baixar_arquivos('pdf', page)
    if download_info_pdf:
        num_nfs = processar_pdf(download_info_pdf)

        df_afazer.at[cliente.Index, 'Notas'] = num_nfs
        dados_obj.registra_numero_notas(cliente.Index, num_nfs)

    gerar_nova_nf(page)

logout(page)
browser.close_browser()
