# Generated by Django 2.2.5 on 2019-11-13 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('photo', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='photo',
            name='md5hash',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
