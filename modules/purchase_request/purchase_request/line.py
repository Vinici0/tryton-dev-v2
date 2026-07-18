from decimal import Decimal

from trytond.model import ModelSQL, ModelView, fields


class PurchaseRequestLine(ModelSQL, ModelView):
    "Línea de Solicitud de Compra"
    __name__ = 'purchase.request.line'

    # FK a la cabecera; CASCADE elimina las líneas si se borra la solicitud
    request = fields.Many2One(
        'purchase.request', "Solicitud",
        required=True, ondelete='CASCADE')
    product = fields.Many2One('product.product', "Producto")
    description = fields.Char("Descripción", required=True)
    quantity = fields.Numeric("Cantidad", digits=(16, 4), required=True)
    unit_price = fields.Numeric("Precio Unitario", digits=(16, 4), required=True)
    # Function field con on_change_with: no persiste en BD y se recalcula
    # en el cliente cada vez que cambian cantidad o precio
    subtotal = fields.Function(
        fields.Numeric("Subtotal", digits=(16, 2)),
        'on_change_with_subtotal')

    @fields.depends('quantity', 'unit_price')
    def on_change_with_subtotal(self, name=None):
        qty = self.quantity or Decimal(0)
        price = self.unit_price or Decimal(0)
        return qty * price

    @fields.depends('product')
    def on_change_product(self):
        # Autocompleta la descripción al seleccionar un producto
        if self.product:
            self.description = self.product.rec_name
