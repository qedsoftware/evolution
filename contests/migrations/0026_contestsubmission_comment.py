# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-03-11 12:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0025_contestsubmission_selected'),
    ]

    operations = [
        migrations.AddField(
            model_name='contestsubmission',
            name='comment',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]