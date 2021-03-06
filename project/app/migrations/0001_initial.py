# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2018-08-09 12:08
from __future__ import unicode_literals

import app.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='cell_mapping',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(blank=True, max_length=50, null=True)),
                ('value', models.CharField(blank=True, max_length=50, null=True)),
                ('field_type', models.CharField(blank=True, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='rc_info',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('result_id', models.IntegerField(blank=True, null=True)),
                ('the_file', models.FileField(blank=True, null=True, upload_to=app.models.file_upload_function)),
                ('org_file_name', models.CharField(blank=True, max_length=300, null=True)),
                ('separator', models.CharField(blank=True, max_length=50, null=True)),
                ('header', models.BooleanField(default=True)),
                ('org_header_file_name', models.CharField(blank=True, max_length=300, null=True)),
                ('header_file', models.FileField(blank=True, null=True, upload_to='media/files/')),
                ('header_separator', models.CharField(blank=True, max_length=10, null=True)),
                ('table_name', models.CharField(blank=True, max_length=50, null=True)),
                ('no_of_rows', models.IntegerField(blank=True, null=True)),
                ('no_of_columns', models.IntegerField(blank=True, null=True)),
                ('database_columns', models.CharField(blank=True, max_length=300, null=True)),
                ('original_columns', models.TextField(blank=True, null=True)),
                ('innova_columns', models.TextField(blank=True, null=True)),
                ('code_column_present', models.BooleanField(default=False)),
                ('code_column_text', models.TextField(blank=True, null=True)),
                ('code_column_row_separator', models.CharField(blank=True, max_length=10, null=True)),
                ('code_column_field_separator', models.CharField(blank=True, max_length=10, null=True)),
                ('code_columns', models.CharField(blank=True, max_length=300, null=True)),
                ('search_columns', models.CharField(blank=True, max_length=300, null=True)),
                ('header_columns', models.CharField(blank=True, max_length=300, null=True)),
                ('body_columns', models.CharField(blank=True, max_length=300, null=True)),
                ('footer_columns', models.CharField(blank=True, max_length=300, null=True)),
                ('uploaded_file_format', models.CharField(blank=True, max_length=10, null=True)),
                ('created_on', models.DateField(auto_now_add=True)),
                ('finalized', models.BooleanField(default=False)),
                ('finalized_on', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='user_profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, max_length=50, null=True)),
                ('last_name', models.CharField(blank=True, max_length=50, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='rc_info',
            name='finalized_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='finalized_by', to='app.user_profile'),
        ),
        migrations.AddField(
            model_name='cell_mapping',
            name='for_record',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='for_record', to='app.rc_info'),
        ),
    ]
