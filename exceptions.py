class ErroNegocio(Exception):
    """Exceção levantada para erros de negócio específicos."""
    pass


class ErroTecnico(Exception):
    """Exceção levantada para erros técnicos ou de sistema."""
    pass


class SystemTimeoutError(ErroTecnico):
    """Exceção levantada para erros técnicos de timeout."""
    pass


class SystemAssertionError(ErroTecnico):
    """Exceção levantada para erros técnicos de asserção."""
    pass
