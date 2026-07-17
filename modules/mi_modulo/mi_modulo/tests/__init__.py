import unittest
from trytond.tests.test_tryton import ModuleTestCase


class MiModuloTestCase(ModuleTestCase):
    "Pruebas de mi_modulo"
    module = 'mi_modulo'


def suite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(MiModuloTestCase))
    return suite
