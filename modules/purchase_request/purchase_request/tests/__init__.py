import unittest
from trytond.tests.test_tryton import ModuleTestCase


class PurchaseRequestTestCase(ModuleTestCase):
    "Pruebas de purchase_request"
    module = 'purchase_request'


def suite():
    suite = unittest.TestSuite()
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(PurchaseRequestTestCase))
    return suite
