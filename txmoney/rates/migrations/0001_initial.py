# coding=utf-8
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='RateSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('base_currency', models.CharField(default=b'EUR', max_length=3, blank=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Rate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('currency', models.CharField(max_length=3)),
                ('value', models.DecimalField(max_digits=14, decimal_places=6)),
                ('date', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.AddField(
            model_name='rate',
            name='source',
            field=models.ForeignKey(
                related_query_name=b'rate', related_name='rates', on_delete=models.PROTECT, to='txmoneyrates.RateSource'
            ),
        ),
        migrations.AlterUniqueTogether(
            name='ratesource',
            unique_together={('name', 'base_currency')},
        ),
        migrations.AlterUniqueTogether(
            name='rate',
            unique_together={('source', 'currency', 'date')},
        ),
    ]
