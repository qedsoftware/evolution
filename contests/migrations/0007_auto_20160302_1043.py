# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-02 10:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0006_conteststage_contestsubmission'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='conteststage',
            name='grader',
        ),
        migrations.RemoveField(
            model_name='contestsubmission',
            name='contest_stage',
        ),
        migrations.AddField(
            model_name='contest',
            name='verification',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='contests.ContestStage'),
            preserve_default=False,
        ),
    ]
