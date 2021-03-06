# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-17 08:57
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import system.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ClientInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('client_address', models.CharField(max_length=255)),
                ('user_agent', models.TextField()),
                ('referer', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invited_email', models.EmailField(max_length=254, validators=[system.models.validate_email_not_used])),
                ('secret_code', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('accepted', models.BooleanField(default=False)),
                ('invited_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='NewsItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField()),
                ('title', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_lang', models.CharField(choices=[('html', 'HTML'), ('plaintext', 'Plain Text'), ('markdown', 'Github-flavored Markdown')], default='markdown', max_length=20)),
                ('source', models.TextField()),
                ('html', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='SystemSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('force_one', models.CharField(default='x', max_length=1, unique=True, validators=[system.models.validate_x])),
                ('footer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='system.Post')),
                ('global_message', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='system.Post')),
            ],
            options={
                'verbose_name': 'System settings',
                'verbose_name_plural': 'System settings',
            },
        ),
        migrations.AddField(
            model_name='newsitem',
            name='content',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='system.Post'),
        ),
    ]
