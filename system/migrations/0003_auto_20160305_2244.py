# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-03-05 22:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import system.models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0002_auto_20160304_0346'),
    ]

    operations = [
        migrations.AddField(
            model_name='systemsettings',
            name='force_one',
            field=models.CharField(default='x', max_length=1, unique=True, validators=[system.models.validate_x]),
        ),
        migrations.AlterField(
            model_name='systemsettings',
            name='footer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='system.Post'),
        ),
    ]