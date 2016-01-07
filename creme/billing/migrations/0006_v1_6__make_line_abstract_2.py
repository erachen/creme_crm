# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations


def copy_old_fields(apps, schema_editor):
    field_names = (
            'cremeentity_ptr',
            'on_the_fly_item',
            'comment',
            'quantity',
            'unit_price',
            'unit',
            'discount',
            'discount_unit',
            'total_discount',
            'vat_value',
        )

    def product_line_model_can_migrate():
        return settings.BILLING_PRODUCT_LINE_MODEL != 'billing.ProductLine'

    def service_line_model_can_migrate():
        return settings.BILLING_SERVICE_LINE_MODEL != 'billing.ServiceLine'

    for model_name, custom_func in [('ProductLine', product_line_model_can_migrate),
                                    ('ServiceLine', service_line_model_can_migrate),
                                   ]:
        if custom_func():
            continue

        for instance in apps.get_model('billing', model_name).objects.all():
            line_instance = instance.line_ptr

            for field_name in field_names:
                setattr(instance, field_name, getattr(line_instance, field_name))

            instance.save()


def remove_old_links(apps, schema_editor):
    # No more 'All lines' view ; so we want to avoid menu items which could cause a 404 error.
    apps.get_model('creme_core', 'PreferedMenuItem').objects \
                                                    .filter(url='/billing/lines') \
                                                    .delete()


def migrate_base_blocks(apps, schema_editor):
    # The block ReceivedBillingDocumentBlock has been removed.
    # We replace it by ReceivedQuotesBlock (Quotes are more important than SalesOrders/CreditNotes).
    apps.get_model('creme_core', 'BlockDetailviewLocation').objects \
                                                           .filter(block_id='block_billing-received_billing_document') \
                                                           .update(block_id='block_billing-received_quotes')


class Migration(migrations.Migration):
    dependencies = [
        ('billing', '0005_v1_6__make_line_abstract_1'),
    ]

    operations = [
        # Step 2: values of Base fields are copied + cleanings.
        migrations.RunPython(copy_old_fields),
        migrations.RunPython(remove_old_links),
        migrations.RunPython(migrate_base_blocks),
    ]
