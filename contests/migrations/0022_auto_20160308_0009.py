# -*- coding: utf-8 -*-
# Generated by Django 1.9.3 on 2016-03-08 00:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0021_auto_20160308_0005'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contest',
            name='published_final_leaderboard',
        ),
        migrations.RemoveField(
            model_name='conteststage',
            name='published_own_results',
        ),
    ]
