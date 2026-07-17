#!/usr/bin/env python3
"""
Seed script: crea datos de prueba en Tryton via Proteus.
Ejecutar con: docker compose exec tryton python /app/scripts/seed.py
Es idempotente: no duplica registros si ya existen.
"""
from decimal import Decimal
from proteus import Model, config

cfg = config.set_trytond(
    database='tryton',
    config_file='/etc/trytond.conf',
)

# ── Moneda ──────────────────────────────────────────────────────────────────
Currency = Model.get('currency.currency')

usd, = Currency.find([('code', '=', 'USD')]) if Currency.find([('code', '=', 'USD')]) else [None]
if not usd:
    usd = Currency(name='US Dollar', code='USD', symbol='$',
                   rounding=Decimal('0.01'))
    usd.save()
    print('✓ Moneda USD creada')
else:
    print('· Moneda USD ya existe')

# ── País ────────────────────────────────────────────────────────────────────
Country = Model.get('country.country')
ec = Country.find([('code', '=', 'EC')])
if ec:
    ec = ec[0]
    print('· País Ecuador ya existe')
else:
    ec = Country(name='Ecuador', code='EC')
    ec.save()
    print('✓ País Ecuador creado')

# ── Empresa principal ────────────────────────────────────────────────────────
Company = Model.get('company.company')
Party  = Model.get('party.party')

companies = Company.find([('party.name', '=', 'Demo Corp')])
if not companies:
    party_co = Party(name='Demo Corp')
    party_co.save()
    company = Company(party=party_co, currency=usd)
    company.save()
    print('✓ Empresa "Demo Corp" creada')
else:
    company = companies[0]
    print('· Empresa "Demo Corp" ya existe')

# ── Clientes de prueba ───────────────────────────────────────────────────────
clientes = [
    ('Cliente Alpha S.A.',   'alpha@demo.com'),
    ('Cliente Beta Cía.',    'beta@demo.com'),
    ('Cliente Gamma Corp.',  'gamma@demo.com'),
]
for nombre, email in clientes:
    existing = Party.find([('name', '=', nombre)])
    if not existing:
        p = Party(name=nombre)
        p.save()
        print(f'✓ Cliente "{nombre}" creado')
    else:
        print(f'· Cliente "{nombre}" ya existe')

# ── Proveedores de prueba ────────────────────────────────────────────────────
proveedores = [
    'Proveedor Uno S.A.',
    'Proveedor Dos Cía.',
]
for nombre in proveedores:
    existing = Party.find([('name', '=', nombre)])
    if not existing:
        p = Party(name=nombre)
        p.save()
        print(f'✓ Proveedor "{nombre}" creado')
    else:
        print(f'· Proveedor "{nombre}" ya existe')

# ── Categoría y productos ────────────────────────────────────────────────────
ProductTemplate = Model.get('product.template')
ProductCategory = Model.get('product.category')
Uom = Model.get('product.uom')

unit_uom = Uom.find([('name', '=', 'Unit')])[0]

cat = ProductCategory.find([('name', '=', 'Demo')])
if not cat:
    cat = ProductCategory(name='Demo')
    cat.save()
    print('✓ Categoría "Demo" creada')
else:
    cat = cat[0]
    print('· Categoría "Demo" ya existe')

# list_price y cost_price son multivalue: requieren contexto de empresa
cfg.set_context({'company': company.id})

productos = [
    ('Producto Demo A', Decimal('10.00')),
    ('Producto Demo B', Decimal('25.50')),
    ('Producto Demo C', Decimal('99.99')),
]
for nombre, precio in productos:
    existing = ProductTemplate.find([('name', '=', nombre)])
    if not existing:
        tmpl = ProductTemplate(
            name=nombre,
            default_uom=unit_uom,
            type='goods',
            list_price=precio,
            cost_price=precio * Decimal('0.6'),
        )
        tmpl.save()
        print(f'✓ Producto "{nombre}" creado')
    else:
        print(f'· Producto "{nombre}" ya existe')

# ── Registros mi_modulo ──────────────────────────────────────────────────────
try:
    Registro = Model.get('mi_modulo.registro')
    registros = [
        ('REG-001', 'Registro Alpha', 'Descripción de prueba Alpha'),
        ('REG-002', 'Registro Beta',  'Descripción de prueba Beta'),
        ('REG-003', 'Registro Gamma', 'Descripción de prueba Gamma'),
    ]
    for codigo, nombre, desc in registros:
        existing = Registro.find([('codigo', '=', codigo)])
        if not existing:
            r = Registro(codigo=codigo, nombre=nombre,
                         descripcion=desc, activo=True)
            r.save()
            print(f'✓ Registro "{codigo}" creado')
        else:
            print(f'· Registro "{codigo}" ya existe')
except Exception as e:
    print(f'⚠ mi_modulo no disponible aún: {e}')

print('\n✅ Seed completado.')
