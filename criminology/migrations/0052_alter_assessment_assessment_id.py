# Generated by Django 5.1.2 on 2024-11-13 11:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criminology', '0051_remove_assessment_period_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessment',
            name='assessment_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]