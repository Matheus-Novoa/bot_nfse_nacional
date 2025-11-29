from patchright.sync_api import expect, Page
from tenacity import retry, wait_fixed, retry_if_exception



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


def gerar_nova_nf(page: Page, browser, primeira=False):
    try:
        if primeira:
            btn_nova_nfse = page.locator("a.btnAcesso[data-original-title='Nova NFS-e']")
            btn_nova_nfse.click()
        else:
            ...
        
    except Exception as e:
        print(f'Erro na geração da nova nota fiscal: {e}')


@retry(retry=retry_if_exception(TimeoutError))
def preencher_tela_pessoas(page: Page, browser):
    try:
        campo_data = page.locator("input.form-control.data")
        expect(campo_data).to_be_editable()
        print('Tela PESSOAS carregada')
        
        campo_data.click()
        campo_data.fill(data)
        page.locator("body").click()

        municipio_prestacao = page.locator(
            "#Prestador_EnderecoNacional_CodigoMunicipio_chosen .chosen-single span"
        )
        expect(municipio_prestacao).not_to_have_text("", timeout=15000)

        localizacao_tomador = page.locator("//div[@id='pnlTomador']//label[contains(.,'Brasil')]/span")
        localizacao_tomador.click()
        
        cpf_tomador = page.locator('#Tomador_Inscricao')
        cpf_tomador.fill(dados['cpf'])
        
        btn_pesquisa_cpf = page.locator("#btn_Tomador_Inscricao_pesquisar")
        btn_pesquisa_cpf.click()

        page.get_by_role("button", name="Avançar").click()
    except Exception as e:
        print(f'SystemError: {e}')
        print('Tentando regarregar a página...')
        try:
            page.reload()
            expect(campo_data).to_be_editable()
            raise TimeoutError
        except Exception as e:
            print(f'SystemError: {e}')
            print('Fechando o sistema...')
            browser.close_browser()


@retry(retry=retry_if_exception(TimeoutError))
def preencher_tela_servicos(page: Page, browser):
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
        page.locator("#ServicoPrestado_Descricao").fill(dados['descricao'])

        campo_nbs = page.locator("#ServicoPrestado_CodigoNBS_chosen")
        campo_nbs.click()
        campo_nbs.locator("input").press_sequentially(nbs_pre.split(' ')[0], delay=50)
        campo_nbs.locator("input").press("Enter")

        page.get_by_role("button", name="Avançar").click()
    except Exception as e:
        print(f'SystemError: {e}')
        print('Tentando regarregar a página...')
        try:
            page.reload()
            expect(campo_municipio).to_be_enabled()
            raise TimeoutError
        except Exception as e:
            print(f'SystemError: {e}')
            print('Fechando o sistema...')
            browser.close_browser()


@retry(retry=retry_if_exception(TimeoutError))
def prencher_tela_valores(page: Page, browser):
    try:
        campo_valor_servico = page.locator('#Valores_ValorServico')
        expect(campo_valor_servico).to_be_editable()
        print('Tela VALORES carregada')

        campo_valor_servico.fill(dados['valor_nota'])
        page.locator("form").click()

        # opcoes_trib_mun = page.locator("//div[@id='pnlOperacaoTributavel']//label[contains(.,'Não')]/span").all()
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
        # page.click("label:has-text('Não Retido') span")

        base_calc = page.locator('#TributacaoFederal_PISCofins_BaseDeCalculo')
        base_calc.fill(dados['valor_nota'])
        # page.fill('#TributacaoFederal_PISCofins_BaseDeCalculo', dados['valor_nota'])

        campo_aliq_pis = page.locator('#TributacaoFederal_PISCofins_AliquotaPIS')
        campo_aliq_pis.fill(aliq_pis)
        # page.fill('#TributacaoFederal_PISCofins_AliquotaPIS', aliq_pis)
        
        campo_aliq_cofins = page.locator('#TributacaoFederal_PISCofins_AliquotaCOFINS')
        campo_aliq_cofins.fill(aliq_cofins)
        # page.fill('#TributacaoFederal_PISCofins_AliquotaCOFINS', aliq_cofins)

        config_valores = page.locator("label:has-text('Configurar os valores percentuais correspondentes') span")
        config_valores.click()
        # page.click("//label[contains(.,'Configurar os valores percentuais correspondentes')]/span")

        percent_fed = page.locator("#ValorTributos_PercentualTotalFederal")
        percent_fed.fill(trib_fed)
        # page.fill('#ValorTributos_PercentualTotalFederal', trib_fed)
        
        percent_est = page.locator("#ValorTributos_PercentualTotalEstadual")
        percent_est.fill(trib_est)
        # page.fill('#ValorTributos_PercentualTotalEstadual', trib_est)
        
        percent_mun = page.locator("#ValorTributos_PercentualTotalMunicipal")
        percent_mun.fill(trib_mun)
        # page.fill('#ValorTributos_PercentualTotalMunicipal', trib_mun)

        page.get_by_role("button", name="Avançar").click()
    except Exception as e:
        print(f'SystemError: {e}')
        print('Tentando regarregar a página...')
        try:
            page.reload()
            expect(campo_valor_servico).to_be_enabled()
            raise TimeoutError
        except Exception as e:
            print(f'SystemError: {e}')
            print('Fechando o sistema...')
            browser.close_browser()