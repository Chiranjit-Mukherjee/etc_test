# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2018-08-18 06:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0005_auto_20180817_0918'),
    ]

    operations = [
        migrations.AddField(
            model_name='rc_info',
            name='body_line_terminator',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='rc_info',
            name='foot_line_terminator',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='rc_info',
            name='head_line_terminator',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='rc_info',
            name='main_line_terminator',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
