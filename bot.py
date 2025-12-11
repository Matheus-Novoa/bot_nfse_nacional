from datetime import datetime
from browser import Browser
from dados import Dados
from web_form import Webform
from logging_config import get_logger


logger = get_logger(__name__)


def main(dataGeracao, pastaDownload, arqPlanilha, sedes):
    sede = [texto for texto, var in sedes.items() if var.get()][0]
    # sede = [texto for texto, var in sedes.items() if var][0] # apenas para teste

    data_obj = datetime.strptime(dataGeracao, '%d/%m/%Y')
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

    dados_obj = Dados(arqPlanilha, sede)

    df_afazer = dados_obj.obter_dados().copy()
    df_afazer['Notas'] = df_afazer['Notas'].astype(str)

    browser = Browser(pastaDownload)
    page = browser.setup_browser()
    webform = Webform(page, browser)

    webform.acessar_portal()
    webform.login()
    webform.gerar_nova_nf(primeira=True)

    for cliente in df_afazer.itertuples():
        webform.cliente = cliente

        webform.preencher_tela_pessoas(dataGeracao)
        webform.preencher_tela_servicos(mes, ano)
        webform.prencher_tela_valores()
        logger.error("Mensagem de erro!!!!!!")
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
