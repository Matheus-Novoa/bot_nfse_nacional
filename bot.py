from patchright.sync_api import sync_playwright, expect
from pathlib import Path


url = 'https://www.nfse.gov.br/EmissorNacional/Login'

data = '17/11/2025'
cpf = '001.965.940-73'
municipio = 'Porto Alegre/RS'
cod_trib_nac_completo = '08.01.01 - Ensino regular pré-escolar, fundamental e médio'
descricao = "descrição"
nbs_pre = '122011200 - Serviços de pré-escola'
nbs_fund = '122012000 - Serviços de ensino fundamental'
valor_nota = '3000,00'
situacao_trib = 'Operação Tributável com Alíquota Básica'
aliq_pis = '1,65'
aliq_cofins = '7,6'
trib_fed = '9,25'
trib_est = '0,00'
trib_mun = '4,00'

browser_dir = Path('browser_dir')
if not browser_dir.exists:
    browser_dir.mkdir(parents=True, exist_ok=True)

play = sync_playwright().start()
context = play.chromium.launch_persistent_context(
    user_data_dir='browser_dir',
    channel='chrome',
    headless=False,
    ignore_https_errors=True,
    args=['--start-maximized']
)
page = context.new_page()
page.goto(url, wait_until='networkidle', timeout=60000)
page.click("//a[@class='img-certificado']")

btn_nova_nfse = page.locator("//a[@class='btnAcesso' and @data-original-title='Nova NFS-e']")
if btn_nova_nfse.is_visible(timeout=60000):
    print('Autenticação bem-sucedida')
    btn_nova_nfse.click()

tela_pessoas = page.locator("//input[@class='form-control data']")
if tela_pessoas.is_visible():
    print('Tela PESSOAS carregada')
    tela_pessoas.fill(data)

    page.wait_for_load_state('networkidle')
    page.click("//input[@name='Prestador.Nome']")

    page.click("//div[@id='pnlTomador']//label[contains(.,'Brasil')]/span")
    page.wait_for_load_state('networkidle')

    page.fill(selector='#Tomador_Inscricao', value=cpf)
    page.click("#btn_Tomador_Inscricao_pesquisar")

    page.get_by_role("button", name="Avançar").click()
else:
    print('Falha na autenticação')

page.locator("#pnlLocalPrestacao").get_by_label("").click()
campo_busca_municipio = page.get_by_role("searchbox", name="Search")
campo_busca_municipio.fill(municipio)
page.wait_for_load_state('networkidle')
page.get_by_role("option", name=municipio).click()

cod_trib_nac_prefix = cod_trib_nac_completo.split()[0].replace('.', '')

page.get_by_label("", exact=True).click()
campo_busca_cod_trib_nac = page.get_by_role("searchbox", name="Search")
campo_busca_cod_trib_nac.fill(cod_trib_nac_prefix)
page.get_by_role("option", name=cod_trib_nac_completo).click()

page.locator("i").nth(1).click()
page.locator("#ServicoPrestado_Descricao").fill(descricao)
page.wait_for_timeout(1000)

campo_nbs = page.locator("#ServicoPrestado_CodigoNBS_chosen")
campo_nbs.click()
campo_nbs.get_by_text(nbs_pre).click()

page.get_by_role("button", name="Avançar").click()

page.fill('#Valores_ValorServico', valor_nota)
page.locator("form").click()

trib_mun = page.locator("//div[@id='pnlOperacaoTributavel']//label[contains(.,'Não')]/span").all()
elegib_issqn = trib_mun[0]
retenc_issqn = trib_mun[1]
beneficio_mun = trib_mun[2]

elegib_issqn.click()
retenc_issqn.click()
beneficio_mun.click()

campo_situacao_trib = page.locator('#TributacaoFederal_PISCofins_SituacaoTributaria_chosen')
campo_situacao_trib.click()
campo_situacao_trib.get_by_text(situacao_trib).click()

page.click("//label[contains(.,'Não Retido')]/span")

page.fill('#TributacaoFederal_PISCofins_BaseDeCalculo', valor_nota)
page.fill('#TributacaoFederal_PISCofins_AliquotaPIS', aliq_pis)
page.fill('#TributacaoFederal_PISCofins_AliquotaCOFINS', aliq_cofins)

page.click("//label[contains(.,'Configurar os valores percentuais correspondentes')]/span")

page.fill('#ValorTributos_PercentualTotalFederal', trib_fed)
page.fill('#ValorTributos_PercentualTotalEstadual', trib_est)
page.fill('#ValorTributos_PercentualTotalMunicipal', trib_mun)

page.get_by_role("button", name="Avançar").click()

cpf_result = page.inner_text("//dt[contains(.,'CPF')]/parent::dl//span")
nome_result = page.inner_text("(//div[@class='pnlCollapse']//dt[contains(.,'Nome')])[2]/following-sibling::dd")
data_result = page.inner_text("(//dt[contains(.,'Data de Competência')]/following-sibling::dd)[1]")
valor_nota_result = page.inner_text("(//dt[contains(.,'Valor do serviço prestado')]/following-sibling::dd)[1]")
situacao_trib_result = page.inner_text("(//dt[contains(.,'Situação Tributária')]/following-sibling::dd)[1]")
base_calc_result = page.inner_text("(//dt[contains(.,'BC')]/following-sibling::dd)[1]")
aliq_pis_result = page.inner_text("(//dt[contains(.,'PIS - Alíquota')]/following-sibling::dd)[1]")
aliq_cofins_result = page.inner_text("(//dt[contains(.,'COFINS - Alíquota')]/following-sibling::dd)[1]")
tipo_reten_result = page.inner_text("(//dt[contains(.,'Tipo de Retenção')]/following-sibling::dd)[1]")

print(cpf_result)
print(nome_result)
print(data_result)
print(valor_nota_result)
print(situacao_trib_result)
print(base_calc_result)
print(aliq_pis_result)
print(aliq_cofins_result)
print(tipo_reten_result)
