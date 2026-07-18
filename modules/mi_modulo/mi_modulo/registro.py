from trytond.model import ModelSQL, ModelView, fields
from trytond.model.modelsql import Unique


class Registro(ModelSQL, ModelView):
    "Registro"
    __name__ = 'mi_modulo.registro'

    codigo = fields.Char("Código", required=True)
    nombre = fields.Char("Nombre", required=True)
    apellido = fields.Char("Apellido")
    descripcion = fields.Text("Descripción")
    activo = fields.Boolean("Activo")

    @classmethod
    def default_activo(cls):
        return True

    @classmethod
    def __setup__(cls):
        super().__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('codigo_unique', Unique(t, t.codigo), 'El código debe ser único.'),
        ]
        cls._order = [('codigo', 'ASC')]
