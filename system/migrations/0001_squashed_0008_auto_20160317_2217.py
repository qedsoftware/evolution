# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-30 09:22
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import system.models


class Migration(migrations.Migration):

    replaces = [('system', '0001_initial'), ('system', '0002_auto_20160304_0346'), ('system', '0003_auto_20160305_2244'), ('system', '0004_auto_20160305_2324'), ('system', '0005_remove_newsitem_author'), ('system', '0006_auto_20160307_1945'), ('system', '0007_invitation'), ('system', '0008_auto_20160317_2217')]

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_lang', models.CharField(max_length=20)),
                ('source', models.TextField()),
                ('html', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='SystemSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('footer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='system.Post')),
                ('global_message', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='system.Post')),
                ('force_one', models.CharField(default='x', max_length=1, unique=True, validators=[system.models.validate_x])),
            ],
        ),
        migrations.CreateModel(
            name='NewsItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('content', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='system.Post')),
                ('title', models.CharField(default='title of the newsitem', max_length=200)),
            ],
        ),
        migrations.AlterField(
            model_name='post',
            name='source_lang',
            field=models.CharField(choices=[('html', 'HTML'), ('plaintext', 'Plain Text'), ('markdown', 'Github-flavored Markdown')], default='markdown', max_length=20),
        ),
        migrations.AlterModelOptions(
            name='systemsettings',
            options={'verbose_name': 'System settings', 'verbose_name_plural': 'System settings'},
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invited_email', models.EmailField(max_length=254, validators=[system.models.validate_email_not_used])),
                ('secret_code', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('invited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('accepted', models.BooleanField(default=False)),
            ],
        ),
    ]
