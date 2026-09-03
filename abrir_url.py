import asyncio
import json
import base64
import gzip
import re
from openpyxl import load_workbook
import pandas as pd
from pathlib import Path
from patchright.async_api import async_playwright
from logging_config import get_logger

logger = get_logger(__name__)


async def obter_notas_afazer(planilha: str):
    try:
        wb = load_workbook(planilha)
        sheet = wb['dados']
    except Exception as e:
        logger.error(f'Falha ao abrir a planilha {planilha}\n{e}')

    if 'Notas' not in [celula.value for celula in sheet[2]]:
        sheet.cell(row=2, column=sheet.max_column + 1).value = 'Notas'
        wb.save(planilha)

    df_planilha = pd.read_excel(planilha, 'dados', header=1)
    return df_planilha[df_planilha['Notas'].isna()]


async def consultar_notas(planilha: str, url: str, xml_dir: Path) -> str:
    xml_dir_path = Path(xml_dir)
    df_afazer = await obter_notas_afazer(planilha)
    
    try:
        wb = load_workbook(planilha)
        sheet = wb['dados']
    except Exception as e:
        logger.error(f'Falha ao abrir a planilha {planilha}\n{e}')

    if 'Notas' not in [celula.value for celula in sheet[2]]:
        sheet.cell(row=2, column=sheet.max_column + 1).value = 'Notas'
    notas_col_index = [celula.value for celula in sheet[2]].index('Notas') + 1

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='browser_dir',
            channel="chrome",
            headless=False
            # args=chrome_args
        )
        page = context.pages[0] if context.pages else await context.new_page()
        print(f"Navegando para: {url}")

        for num_linha, conteudo_linha in df_afazer.iterrows():
            await page.goto(url + conteudo_linha['Chave'], wait_until="domcontentloaded")
            print("Página carregada com sucesso!")

            await page.locator("pre").wait_for(state="visible", timeout=5000)
            texto_bruto = await page.locator("pre").inner_text()
            dados_json = json.loads(texto_bruto)
            dados_base64 = dados_json['nfseXmlGZipB64'].strip()

            dados_xml = base64.b64decode(dados_base64)
        
            try:
                xml_descompactado = gzip.decompress(dados_xml)
                resultado = re.search(rb'<nNFSe>(\d+)</nNFSe>', xml_descompactado)
                if resultado:
                    numero_nota = int(resultado.group(1).decode('utf-8'))
                    print(f"Número da NFSe encontrado: {numero_nota}")
                else:
                    print("A tag <nNFSe> não foi encontrada na string.")

                with open(xml_dir_path / f"nfse_{numero_nota:0>4}.xml", "wb") as f:
                    f.write(xml_descompactado)
                print("Sucesso! O XML estava compactado em GZ e foi extraído com êxito.")
            except Exception as e:
                # 2. Se não for GZ, salva os bytes puros como ZIP ou PDF para você testar abrir manualmente
                with open(xml_dir_path / f"nfse_{numero_nota:0>4}.zip", "wb") as f:
                    f.write(dados_xml)
                print("Não era GZIP. Os dados brutos foram salvos em 'arquivo_desconhecido.zip'.")
                print("Tente extrair esse arquivo ZIP ou renomeá-lo para .pdf para testar.")

            sheet.cell(row=num_linha+3, column=notas_col_index).value = numero_nota
        wb.save(planilha)


if __name__ == "__main__":
    url = 'https://sefin.nfse.gov.br/SefinNacional/nfse/'
    planilha = r"C:\Users\novoa\OneDrive\Área de Trabalho\notas_MB\planilhas\zona_norte\escola_canadenseZS_jul26\Maple Bear Zona Norte Jul 26.xlsx"
    xml_dir = r'C:\Users\novoa\OneDrive\Área de Trabalho\notas_MB\xml_notas_jul'
    # print(asyncio.run(obter_notas_afazer(planilha)))
    asyncio.run(
        consultar_notas(
            planilha,
            url,
            xml_dir
        )
    )