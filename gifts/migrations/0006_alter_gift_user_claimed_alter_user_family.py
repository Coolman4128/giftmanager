# Generated by Django 5.1.3 on 2024-11-28 23:43

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gifts', '0005_alter_gift_family_alter_gift_user_claimed_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gift',
            name='user_claimed',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='user_claimed', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='user',
            name='family',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gifts.family'),
        ),
    ]
