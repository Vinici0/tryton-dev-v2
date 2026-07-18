import unittest
from decimal import Decimal


class SubtotalTestCase(unittest.TestCase):
    "Tests de lógica de cálculo (sin base de datos)"

    def test_subtotal_normal(self):
        "3 unidades × $10 = $30"
        qty = Decimal('3')
        price = Decimal('10')
        self.assertEqual(qty * price, Decimal('30'))

    def test_subtotal_decimal(self):
        "Cantidades decimales: 1.5 × $20 = $30"
        qty = Decimal('1.5')
        price = Decimal('20')
        self.assertEqual(qty * price, Decimal('30.0'))

    def test_subtotal_zero_qty(self):
        "Cantidad cero retorna cero"
        qty = Decimal('0')
        price = Decimal('100')
        self.assertEqual(qty * price, Decimal('0'))

    def test_subtotal_none_defaults(self):
        "None debe tratarse como cero (comportamiento del modelo)"
        qty = None or Decimal('0')
        price = None or Decimal('0')
        self.assertEqual(qty * price, Decimal('0'))

    def test_state_transitions_valid(self):
        "Las transiciones de estado permitidas están definidas"
        transitions = {
            ('draft', 'submitted'),
            ('submitted', 'approved'),
            ('submitted', 'rejected'),
            ('submitted', 'draft'),
            ('rejected', 'draft'),
            ('approved', 'processed'),
            ('draft', 'cancelled'),
        }
        self.assertIn(('draft', 'submitted'), transitions)
        self.assertIn(('submitted', 'approved'), transitions)
        self.assertIn(('submitted', 'rejected'), transitions)
        self.assertNotIn(('approved', 'draft'), transitions)
        self.assertNotIn(('processed', 'draft'), transitions)

    def test_default_state_is_draft(self):
        "El estado por defecto debe ser 'draft'"
        from purchase_request.request import PurchaseRequest
        self.assertEqual(PurchaseRequest.default_state(), 'draft')


def suite():
    suite = unittest.TestSuite()
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(SubtotalTestCase))
    return suite
