# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-24 20:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0005_auto_20160223_1628'),
    ]

    operations = [
        migrations.RenameField(
            model_name='submission',
            old_name='answer',
            new_name='output',
        ),
        migrations.AddField(
            model_name='datagrader',
            name='time_limit_ms',
            field=models.IntegerField(default=1000),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='gradingattempt',
            name='log',
            field=models.FileField(default=1, upload_to=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='gradingattempt',
            name='started',
            field=models.BooleanField(default=False),
        ),
    ]