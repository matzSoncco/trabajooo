# Generated by Django 5.0.6 on 2024-08-06 01:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('almacen', '0002_toolloan_delete_loan'),
    ]

    operations = [
        migrations.AlterField(
            model_name='toolloan',
            name='worker',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tool_loans', to='almacen.worker'),
        ),
    ]
