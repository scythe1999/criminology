# Generated by Django 5.1.2 on 2024-11-09 14:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('criminology', '0049_rename_analyzing_assesment_assesment_analyzing_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Assesment',
            new_name='Assessment',
        ),
        migrations.RenameField(
            model_name='assessment',
            old_name='assesment_id',
            new_name='assessment_id',
        ),
    ]