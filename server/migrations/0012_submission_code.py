# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-08 09:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0011_auto_20160408_1720'),
    ]

    operations = [
        migrations.AddField(
            model_name='submission',
            name='code',
            field=models.TextField(blank=True, null=True),
        ),
    ]
