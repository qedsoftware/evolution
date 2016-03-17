# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-17 22:17
from __future__ import unicode_literals

from django.db import migrations, models
import system.models


class Migration(migrations.Migration):

    dependencies = [
        ('system', '0007_invitation'),
    ]

    operations = [
        migrations.AddField(
            model_name='invitation',
            name='accepted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='invitation',
            name='invited_email',
            field=models.EmailField(max_length=254, validators=[system.models.validate_email_not_used]),
        ),
    ]
