# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-25 11:50
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0002_auto_20160425_1146'),
    ]

    operations = [
        migrations.RenameField(
            model_name='systemsettings',
            old_name='force_one',
            new_name='force_singleton',
        ),
    ]
