# Generated by Django 2.2.24 on 2021-12-23 13:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('photo', '0003_auto_20191113_1617'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='tagprops',
            unique_together={('tag', 'name')},
        ),
    ]