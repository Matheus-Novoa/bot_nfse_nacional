from unicodedata import normalize
import re
from rapidfuzz import fuzz, process

def normalizar_texto(texto: str) -> str:
    """
    Remove acentos, caracteres especiais e converte para minúsculas.
    Exemplo: "João da Silva" -> "joao da silva"
    """
    if not texto:
        return ""

    texto_minusc_sem_acentos = (
        normalize('NFKD', texto)
        .encode('ascii', 'ignore')
        .decode('ascii').lower()
    )
    texto_normalizado = re.sub(r'[^a-z\s]', '', texto_minusc_sem_acentos)
    return " ".join(texto_normalizado.split())


def validar_nome(nome_planilha, nome_portal, limite=95):
    """
    Valida nomes mesmo que falte o sobrenome do meio.
    """
    n1 = normalizar_texto(nome_planilha)
    n2 = normalizar_texto(nome_portal)

    if not n1 or not n2:
        return False

    # O token_set_ratio é ideal para subconjuntos de palavras.
    # Ele separa as palavras e verifica se as de uma string estão na outra.
    score = fuzz.token_set_ratio(n1, n2)
    print(score)
    return score >= limite


def validar_nome_lista(nome_planilha, lista_nomes_base, limite=85):
    """
    Valida um nome contra uma lista de nomes, retornando o melhor match.
    """
    n1 = normalizar_texto(nome_planilha)
    
    if not n1:
        return None
    
    return process.extractOne(
        query=n1,
        choices=lista_nomes_base,
        scorer=fuzz.token_set_ratio,
        score_cutoff=limite
    )


if __name__ == "__main__":
    # Testes simples
    print('Thiago Josué Bem', '-->', validar_nome("THIAGO JOSUE BEN", "Thiago Josué Bem"), '\n')
    print('Pablo Felipe Bondam', '-->', validar_nome("PABLO FELIPE BONDAN", "Pablo Felipe Bondam"), '\n')
    print("Marcos D'arrigo Mottin", '-->', validar_nome("MARCOS D ARRIGO MOTTIN", "Marcos D'arrigo Mottin"), '\n')
    print('Luiz Antonio P dos Santos Jr', '-->', validar_nome("LUIZ ANTONIO PAIM DOS SANTOS JUNIOR", "Luiz Antonio P dos Santos Jr"), '\n')
    print('Marcela Ramos Izolan', '-->', validar_nome("MARCELA ROSA IZOLAN", "Marcela Ramos Izolan"), '\n')
    print('Fedelle Rafaelle Aronna', '-->', validar_nome("FEDELE RAFFAELE ARONNA", "Fedelle Rafaelle Aronna"), '\n')
    print('Weverson L Oliveiro Moura ', '-->', validar_nome("WEVERSON LEANDRO OLIVEIRA MOURA", "Weverson L Oliveiro Moura "), '\n')
    print('Juliana C Gonçalves', '-->', validar_nome("JULIANA CORREIA GONCALVES", "Juliana C Gonçalves"), '\n')
    print('André A F Piletti', '-->', validar_nome("ANDRE AUGUSTO FREITAS PILETTI", "André A F Piletti"), '\n')
    print('Gleice Cristina Bruno', '-->', validar_nome("BENICIO BRUNO DE ANDRADE", "Gleice Cristina Bruno"), '\n')
