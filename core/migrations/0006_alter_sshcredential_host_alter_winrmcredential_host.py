# Generated by Django 5.1.6 on 2025-03-08 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_remove_host_ssh_credential_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sshcredential',
            name='host',
            field=models.ManyToManyField(blank=True, to='core.host'),
        ),
        migrations.AlterField(
            model_name='winrmcredential',
            name='host',
            field=models.ManyToManyField(blank=True, to='core.host'),
        ),
    ]
