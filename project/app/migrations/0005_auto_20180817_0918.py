# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2018-08-17 09:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_auto_20180817_0607'),
    ]

    operations = [
        migrations.AddField(
            model_name='rc_info',
            name='body_primary_field',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='rc_info',
            name='footer_primary_field',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
        migrations.AddField(
            model_name='rc_info',
            name='head_primary_field',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
