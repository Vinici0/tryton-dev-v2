from datetime import date
from decimal import Decimal

from trytond.exceptions import UserError
from trytond.i18n import gettext
from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import Pool
from trytond.pyson import Eval
from trytond.transaction import Transaction

# Estados posibles de una solicitud de compra
STATES = [
    ('draft', 'Borrador'),
    ('submitted', 'Enviada'),
    ('approved', 'Aprobada'),
    ('rejected', 'Rechazada'),
    ('processed', 'Atendida'),
    ('cancelled', 'Cancelada'),
]

# PYSON reutilizable: todos los campos se bloquean al salir de Borrador
_READONLY = {'readonly': Eval('state') != 'draft'}


class PurchaseRequest(ModelSQL, ModelView):
    "Solicitud de Compra"
    __name__ = 'purchase.request'

    number = fields.Char("Número", readonly=True)
    date = fields.Date("Fecha", required=True, states=_READONLY)
    party = fields.Many2One(
        'party.party', "Solicitante", required=True, states=_READONLY)
    department = fields.Char("Departamento", states=_READONLY)
    supplier = fields.Many2One(
        'party.party', "Proveedor Sugerido", states=_READONLY)
    description = fields.Text("Justificación", states=_READONLY)
    # One2Many inverso del Many2One 'request' en PurchaseRequestLine
    lines = fields.One2Many(
        'purchase.request.line', 'request', "Productos", states=_READONLY)
    # Campo calculado: suma los subtotales de todas las líneas
    subtotal = fields.Function(
        fields.Numeric("Total", digits=(16, 2)), 'get_subtotal')
    state = fields.Selection(STATES, "Estado", required=True, readonly=True)
    rejection_reason = fields.Text(
        "Motivo de Rechazo",
        states={
            'invisible': ~Eval('state').in_(['submitted', 'rejected']),
            'readonly': Eval('state') == 'rejected',
        })
    approved_by = fields.Many2One('res.user', "Aprobado por", readonly=True)
    approved_date = fields.Date("Fecha de Aprobación", readonly=True)

    @classmethod
    def default_state(cls):
        return 'draft'

    @classmethod
    def default_date(cls):
        return date.today()

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._order = [('date', 'DESC'), ('id', 'DESC')]
        # Visibilidad de botones controlada por PYSON según el estado actual
        cls._buttons.update({
            'submit': {
                'invisible': Eval('state') != 'draft',
                'depends': ['state'],
            },
            'approve': {
                'invisible': Eval('state') != 'submitted',
                'depends': ['state'],
            },
            'reject': {
                'invisible': Eval('state') != 'submitted',
                'depends': ['state'],
            },
            'mark_processed': {
                'invisible': Eval('state') != 'approved',
                'depends': ['state'],
            },
            'reset_to_draft': {
                'invisible': ~Eval('state').in_(['submitted', 'rejected']),
                'depends': ['state'],
            },
            'cancel': {
                'invisible': Eval('state') != 'draft',
                'depends': ['state'],
            },
        })

    @classmethod
    def get_rec_name(cls, records, name):
        # El nombre visible del registro en relaciones y búsquedas
        return {r.id: r.number or str(r.id) for r in records}

    @classmethod
    def get_subtotal(cls, requests, name):
        # Getter en batch: recibe todos los registros a la vez para evitar
        # una query por registro
        result = {}
        for request in requests:
            result[request.id] = sum(
                (line.subtotal or Decimal(0)) for line in request.lines)
        return result

    @classmethod
    @ModelView.button
    def submit(cls, requests):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        SequenceType = pool.get('ir.sequence.type')

        # Buscar la secuencia SC-XXXXXX; si no existe el número queda vacío
        types = SequenceType.search(
            [('name', '=', 'Solicitud de Compra')], limit=1)
        seq = None
        if types:
            seqs = Sequence.search(
                [('sequence_type', '=', types[0].id)], limit=1)
            if seqs:
                seq = seqs[0]

        # cls.write() acepta pares [lista, valores] encadenados en una sola
        # llamada para evitar una query UPDATE por registro
        to_write = []
        for request in requests:
            if request.state != 'draft':
                continue
            if not request.lines:
                raise UserError(
                    gettext('purchase_request.msg_lines_required'))
            number = request.number
            if not number and seq:
                number = seq.get()  # genera SC-000001, SC-000002, etc.
            to_write.extend([
                [request],
                {'state': 'submitted', 'number': number},
            ])
        if to_write:
            cls.write(*to_write)

    @classmethod
    @ModelView.button
    def approve(cls, requests):
        # Guarda quién aprobó y cuándo usando el usuario de la sesión activa
        user_id = Transaction().user
        to_write = []
        for request in requests:
            if request.state != 'submitted':
                continue
            to_write.extend([
                [request],
                {
                    'state': 'approved',
                    'approved_date': date.today(),
                    'approved_by': user_id,
                },
            ])
        if to_write:
            cls.write(*to_write)

    @classmethod
    @ModelView.button
    def reject(cls, requests):
        to_write = []
        for request in requests:
            if request.state != 'submitted':
                continue
            # Motivo obligatorio antes de rechazar
            if not request.rejection_reason:
                raise UserError(
                    gettext('purchase_request.msg_rejection_reason_required'))
            to_write.extend([[request], {'state': 'rejected'}])
        if to_write:
            cls.write(*to_write)

    @classmethod
    @ModelView.button
    def mark_processed(cls, requests):
        to_write = [[r for r in requests if r.state == 'approved'],
                    {'state': 'processed'}]
        if to_write[0]:
            cls.write(*to_write)

    @classmethod
    @ModelView.button
    def reset_to_draft(cls, requests):
        to_write = [
            [r for r in requests if r.state in ('submitted', 'rejected')],
            {'state': 'draft', 'approved_date': None, 'approved_by': None},
        ]
        if to_write[0]:
            cls.write(*to_write)

    @classmethod
    @ModelView.button
    def cancel(cls, requests):
        to_write = [[r for r in requests if r.state == 'draft'],
                    {'state': 'cancelled'}]
        if to_write[0]:
            cls.write(*to_write)

    @classmethod
    def delete(cls, requests):
        # Solo se pueden eliminar solicitudes en Borrador
        for request in requests:
            if request.state != 'draft':
                raise UserError(
                    gettext('purchase_request.msg_delete_draft_only'))
        super().delete(requests)
