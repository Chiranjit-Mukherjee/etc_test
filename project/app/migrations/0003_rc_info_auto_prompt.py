# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2018-08-16 05:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20180814_1013'),
    ]

    operations = [
        migrations.AddField(
            model_name='rc_info',
            name='auto_prompt',
            field=models.TextField(blank=True, null=True),
        ),
    ]
