from django.db import migrations


def set_contact_links(apps, schema_editor):
    configuration = apps.get_model('store', 'StoreConfiguration')
    configuration.objects.using(schema_editor.connection.alias).update_or_create(
        pk=1,
        defaults={
            'whatsapp': '917454940300',
            'facebook': 'https://www.facebook.com/KedarkhandGlobalVentures/',
            'instagram': 'https://www.instagram.com/kgv.2026/?__pwa=1#',
        },
    )


class Migration(migrations.Migration):
    dependencies = [('store', '0004_alter_category_slug_alter_product_category_and_more')]
    operations = [migrations.RunPython(set_contact_links, migrations.RunPython.noop)]
