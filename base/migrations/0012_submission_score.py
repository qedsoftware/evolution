# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-03-07 19:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0011_gradingattempt_finished_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='score',
            field=models.DecimalField(decimal_places=6, max_digits=30, null=True),
        ),
    ]
