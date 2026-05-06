import pandas as pd
from pathlib import Path
from openpyxl import load_workbook
from logging_config import get_logger
from exceptions import ErroNegocio, ErroTecnico
from config import obter_dados_config
from utils.valida_nomes import normalizar_texto, validar_nome_lista


logger = get_logger(__name__)


class Dados:
    def __init__(self, arqPlanilha, sede):
        self.arqPlanilha = Path(arqPlanilha)
        self.config = obter_dados_config()

        if sede == 'Matriz':
            self.base_df = pd.read_excel(self.config['base_matriz'], usecols=["ResponsávelFinanceiro", "CPF"])
        else:
            self.base_df = pd.read_excel(self.config['base_filial'], usecols=["ResponsávelFinanceiro", "CPF"])


    def limpar_cpf(self, cpf):
        """
        Limpa o CPF: remove decimais, mantém apenas dígitos, trata NaNs e preenche com zeros até 11 dígitos.
        Retorna None se for NaN ou inválido.
        """
        if pd.isna(cpf):
            return ''
        cpf_str = str(cpf).split('.')[0]  # Remove decimais (ex.: "123456789012.0" -> "123456789012")
        return cpf_str.zfill(11)
        

    def encontrar_melhor_match(self, nome):
        """
        Recebe um nome e retorna uma tupla contendo:
        - o nome da base de dados que mais se aproxima do nome informado;
        - o CPF associado a esse nome.
        Caso nenhum nome seja encontrado, retorna (None, None).
        """
        base_normalizada = self.base_df.copy() 
        base_normalizada['CPF'] = base_normalizada['CPF'].astype(str)
        base_normalizada['CPF'] = base_normalizada['CPF'].str.zfill(11).astype(str)  # Garantir que o CPF tenha 11 dígitos
        base_normalizada["ResponsávelFinanceiro"] = base_normalizada["ResponsávelFinanceiro"].apply(normalizar_texto)
     
        lista_nomes = base_normalizada["ResponsávelFinanceiro"].tolist()
        correspondencia = validar_nome_lista(nome, lista_nomes)
        
        if correspondencia:
            melhor_nome = correspondencia[0]
            cpf = base_normalizada.loc[base_normalizada.iloc[:, 0] == melhor_nome].iloc[0, 1]
        else:
            nome = None
            cpf = None

        return nome, cpf
    
    
    def formata_planilha(self, arqPlanilha):
        try:
            wb = load_workbook(arqPlanilha)
        except Exception as e:
            logger.error(f'Falha ao abrir a planilha {arqPlanilha}\n{e}')
            raise ErroTecnico(f'Falha ao abrir a planilha {arqPlanilha}\n{e}')


        if not 'dados' in wb.sheetnames:
            self.dados_origem = pd.read_excel(arqPlanilha, 'dados_origem', header=1, skipfooter=1)

            resultado = self.dados_origem["ResponsávelFinanceiro"].apply(
                lambda nome: pd.Series(self.encontrar_melhor_match(nome), index=["ResponsávelFinanceiro", "CPF"])
            )
            self.dados_destino = self.dados_origem.drop(columns=["ResponsávelFinanceiro", "CPF"]).join(resultado)

            dados_faltantes = self.dados_destino['ResponsávelFinanceiro'].isna()
            clientes_novos = pd.DataFrame()
            if dados_faltantes.any():
                clientes_novos = self.dados_origem.loc[dados_faltantes]

                logger.info('Clientes não cadastrados encontrados')
                logger.info('\n' + '\n'.join(clientes_novos['ResponsávelFinanceiro'].to_list()))

            with pd.ExcelWriter(arqPlanilha, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
                self.dados_destino.to_excel(writer, sheet_name="dados", index=False, startrow=1)
                if not clientes_novos.empty:
                    clientes_novos.to_excel(writer, sheet_name="clientes_novos", index=False)


    def obter_dados(self, a_fazer=True):
        try:
            wb = load_workbook(self.arqPlanilha)
        except Exception as e:
            logger.error(f'Falha ao abrir a planilha {self.arqPlanilha}\n{e}')
            raise ErroTecnico(f'Falha ao abrir a planilha {self.arqPlanilha}\n{e}')

        if 'dados' in wb.sheetnames:
            self.dados = pd.read_excel(self.arqPlanilha, 'dados', header=1)#, skipfooter=1)

            if 'Notas' not in self.dados.columns:
                self.dados['Notas'] = None
            
            self.dados['Aluno'] = self.dados['Aluno'].apply(lambda i: i.split()[0])
            # Garantir que o CPF seja tratado como string, sem casas decimais. Não imputar valores às células vazias
            self.dados['CPF'] = self.dados['CPF'].apply(self.limpar_cpf)

            self.dados.loc[self.dados['Turma'].str.contains('Y1|Y2|Year'), 'Acumulador'] = '2'
            self.dados['Acumulador'] = self.dados['Acumulador'].fillna('1')

            self.dados['Mensalidade'] = self.dados['Mensalidade'].apply(lambda x: '{:0.2f}'.format(x).replace('.',','))
            self.dados['ValorTotal'] = self.dados['ValorTotal'].apply(lambda x: '{:0.2f}'.format(x).replace('.',','))
            self.dados['Alimentação'] = self.dados['Alimentação'].apply(lambda x: '{:0.2f}'.format(x).replace('.',','))

            return self.dados[self.dados['Notas'].isna()] if a_fazer else self.dados
        else:
            logger.error("A aba 'dados' não existe na planilha")
            raise ErroNegocio(
                "A aba 'dados' não existe na planilha"
            )
    

    def registra_numero_notas(self, index_df, num_nota):
        if not isinstance(index_df, int):
            logger.error("index_df deve ser um inteiro")
            raise ErroNegocio("index_df deve ser um inteiro")
        if not isinstance(num_nota, int):
            logger.error("num_nota deve ser um inteiro")
            raise ErroNegocio("num_nota deve ser um inteiro")
            
        try:
            wb = load_workbook(self.arqPlanilha)
            sheet = wb['dados']
        except Exception as e:
            logger.error(f'Falha ao abrir a planilha {self.arqPlanilha}\n{e}')
            raise ErroTecnico(f'Falha ao abrir a planilha {self.arqPlanilha}\n{e}')

        # Adicionar a coluna 'Status' se não existir
        if 'Notas' not in [celula.value for celula in sheet[2]]:
            sheet.cell(row=2, column=sheet.max_column + 1).value = 'Notas'

        notas_col_index = [celula.value for celula in sheet[2]].index('Notas') + 1
        sheet.cell(row=index_df+3, column=notas_col_index).value = num_nota

        try:
            wb.save(self.arqPlanilha)
        except Exception as e:
            logger.error(f'Falha ao salvar a planilha {self.arqPlanilha}\n{e}')
            raise ErroTecnico(f'Falha ao salvar a planilha {self.arqPlanilha}\n{e}')



if __name__ == '__main__':
    arquivo_planilha = r"C:\Users\novoa\OneDrive\Área de Trabalho\notas_MB\planilhas\zona_sul\escola_canadenseZS_nov25\Numeração de Boletos_Zona Sul_2025_NOVEMBRO.xlsx"
    dados = Dados(arquivo_planilha, 'Matriz')
    n = dados.encontrar_melhor_match("Lilian C Souza de Lima Abdon")
    print(n)
    # df = dados.obter_dados()#a_fazer=False)
    # print(df)
