# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-23 13:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datagrader',
            name='answer_file',
        ),
        migrations.AddField(
            model_name='datagrader',
            name='answer',
            field=models.FileField(null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='submission',
            name='answer',
            field=models.FileField(null=True, upload_to=''),
        ),
    ]
