from datetime import datetime
from browser import Browser
from dados import Dados
from web_form import Webform
from logging_config import get_logger, enviar_log_telegram


logger = get_logger(__name__)


async def main(dataGeracao, pastaDownload, arqPlanilha, sedes):
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
    webform = await Webform.create(page, browser)

    try:
        await webform.acessar_portal()
        await webform.login()
        await webform.gerar_nova_nf(primeira=True)

        for cliente in df_afazer.itertuples():
            webform.cliente = cliente

            await webform.preencher_tela_pessoas(dataGeracao)
            await webform.preencher_tela_servicos(mes, ano)
            await webform.prencher_tela_valores()
            await webform.emitir_nota()
            
            download_info_pdf = await webform.baixar_arquivos('pdf')
            if download_info_pdf:
                num_nfs = await webform.processar_pdf(download_info_pdf)

                df_afazer.at[cliente.Index, 'Notas'] = num_nfs
                dados_obj.registra_numero_notas(cliente.Index, num_nfs)
            
            download_info_xml = await webform.baixar_arquivos('xml')
            if download_info_xml:
                await webform.salvar_xml(download_info_xml, num_nfs)

            await webform.gerar_nova_nf()
    except Exception as e:
        logger.error(e)
        await enviar_log_telegram(f'Erro:\n{e}')
    finally:
        await webform.logout()
        await browser.close_browser()
        await enviar_log_telegram('Processo finalizado')
