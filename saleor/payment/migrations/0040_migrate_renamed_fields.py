from django.apps import apps as registry
from django.db import migrations
from django.db.models.signals import post_migrate

from .tasks.saleor3_12 import (
    transaction_event_migrate_name_to_message,
    transaction_event_migrate_reference_to_psp_reference,
    transaction_item_migrate_reference_to_psp_reference,
    transaction_item_migrate_type_to_name,
    transaction_item_migrate_voided_to_canceled,
)


def migrate_data_for_renamed_fields(apps, _schema_editor):
    def on_migrations_complete(sender=None, **kwargs):
        transaction_event_migrate_name_to_message.delay()
        transaction_event_migrate_reference_to_psp_reference.delay()
        transaction_item_migrate_reference_to_psp_reference.delay()
        transaction_item_migrate_type_to_name.delay()
        transaction_item_migrate_voided_to_canceled.delay()

    sender = registry.get_app_config("payment")
    post_migrate.connect(on_migrations_complete, weak=False, sender=sender)


class Migration(migrations.Migration):
    dependencies = [
        ("payment", "0039_transactionevent_currency"),
    ]

    operations = [
        migrations.RunPython(migrate_data_for_renamed_fields, migrations.RunPython.noop)
    ]