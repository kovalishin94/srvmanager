# Generated by Django 5.1.6 on 2025-04-06 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ops', '0005_sendfile_file_alter_sendfile_local_path'),
    ]

    operations = [
        migrations.AddField(
            model_name='executecommand',
            name='sudo',
            field=models.BooleanField(default=False),
        ),
    ]
