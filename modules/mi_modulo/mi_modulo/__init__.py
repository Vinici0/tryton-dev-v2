from trytond.pool import Pool
from . import registro


def register():
    Pool.register(
        registro.Registro,
        module='mi_modulo',
        type_='model',
    )
