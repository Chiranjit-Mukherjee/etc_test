# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2018-08-24 12:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0010_replicate_records'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='replicate_records',
            name='created_by',
        ),
        migrations.RemoveField(
            model_name='replicate_records',
            name='new_record',
        ),
        migrations.RemoveField(
            model_name='replicate_records',
            name='replicated_record',
        ),
        migrations.AddField(
            model_name='rc_info',
            name='replicated_from',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.DeleteModel(
            name='replicate_records',
        ),
    ]
