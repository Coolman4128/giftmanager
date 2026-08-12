from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_gift_creators(apps, schema_editor):
    Gift = apps.get_model('gifts', 'Gift')
    for gift in Gift.objects.all().iterator():
        gift.created_by_id = gift.user_paired_id
        gift.save(update_fields=['created_by'])


class Migration(migrations.Migration):

    dependencies = [
        ('gifts', '0007_alter_gift_link'),
    ]

    operations = [
        migrations.AddField(
            model_name='gift',
            name='created_by',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='gifts_created',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(backfill_gift_creators, migrations.RunPython.noop),
    ]
