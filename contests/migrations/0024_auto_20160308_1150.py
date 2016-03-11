# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-03-08 11:50
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0023_auto_20160308_0059'),
    ]

    operations = [
        migrations.AddField(
            model_name='conteststage',
            name='requires_selection',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='conteststage',
            name='selected_limit',
            field=models.IntegerField(default=-1),
        ),
        migrations.AlterField(
            model_name='contestsubmission',
            name='team',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contests.Team'),
        ),
    ]