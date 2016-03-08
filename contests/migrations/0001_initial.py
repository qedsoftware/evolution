# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-23 17:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('base', '0005_auto_20160223_1628'),
        ('system', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Contest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='system.Post')),
                ('test', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.DataGrader')),
                ('verification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='base.DataGrader')),
            ],
        ),
    ]