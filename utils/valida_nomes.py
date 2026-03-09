import unicodedata
import re
from rapidfuzz import fuzz

def normalizar(texto):
    """
    Remove acentos, caracteres especiais e converte para minúsculas.
    Exemplo: "João da Silva" -> "joao da silva"
    """
    if not texto:
        return ""

    texto_minusc_sem_acentos = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii').lower()
    texto_normalizado = re.sub(r'[^a-z\s]', '', texto_minusc_sem_acentos)
    return " ".join(texto_normalizado.split())


def validar_nome(nome_planilha, nome_portal, limite=95):
    """
    Valida nomes mesmo que falte o sobrenome do meio.
    """
    n1 = normalizar(nome_planilha)
    n2 = normalizar(nome_portal)

    if not n1 or not n2:
        return False

    # O token_set_ratio é ideal para subconjuntos de palavras.
    # Ele separa as palavras e verifica se as de uma string estão na outra.
    score = fuzz.token_set_ratio(n1, n2)
    return score >= limite
