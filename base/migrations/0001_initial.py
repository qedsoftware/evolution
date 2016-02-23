# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-23 02:53
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataGrader',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer_file', models.FileField(upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='GradingAttempt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('finished', models.BooleanField(default=False)),
                ('succed', models.BooleanField(default=False)),
                ('score', models.DecimalField(decimal_places=6, max_digits=30, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='ScoringScript',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source', models.FileField(upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('answer', models.FileField(upload_to='')),
                ('score', models.DecimalField(decimal_places=6, max_digits=30, null=True)),
                ('current_attempt', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='base.GradingAttempt')),
                ('grader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.DataGrader')),
            ],
        ),
        migrations.AddField(
            model_name='gradingattempt',
            name='submission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='base.Submission'),
        ),
        migrations.AddField(
            model_name='datagrader',
            name='scoring_script',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='base.ScoringScript'),
        ),
    ]
