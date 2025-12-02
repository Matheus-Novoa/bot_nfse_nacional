from datetime import datetime
from adapters import BrowserAdapter
from dados import Dados
from web_form import Webform


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

browser = BrowserAdapter()
page = browser.setup_browser()
webform = Webform(page, browser)

webform.acessar_portal(url)
webform.login()
webform.gerar_nova_nf(primeira=True)

for cliente in df_afazer.itertuples():
    webform.cliente = cliente

    webform.preencher_tela_pessoas(data)
    webform.preencher_tela_servicos(
        municipio,
        cod_trib_nac_completo,
        mes,
        ano,
        nbs_pre,
        nbs_fund
    )
    webform.prencher_tela_valores(
        situacao_trib,
        aliq_pis,
        aliq_cofins,
        trib_fed,
        trib_est,
        trib_mun
    )
    webform.emitir_nota()
    
    download_info_xml = webform.baixar_arquivos('xml')
    if download_info_xml:
        webform.salvar_xml(download_info_xml)

    download_info_pdf = webform.baixar_arquivos('pdf')
    if download_info_pdf:
        num_nfs = webform.processar_pdf(download_info_pdf)

        df_afazer.at[cliente.Index, 'Notas'] = num_nfs
        dados_obj.registra_numero_notas(cliente.Index, num_nfs)

    webform.gerar_nova_nf()

webform.logout()
browser.close_browser()
