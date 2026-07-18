from trytond.pool import Pool
from . import request, line


def register():
    Pool.register(
        request.PurchaseRequest,
        line.PurchaseRequestLine,
        module='purchase_request',
        type_='model',
    )
