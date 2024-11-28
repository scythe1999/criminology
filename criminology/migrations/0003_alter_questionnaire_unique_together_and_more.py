# Generated by Django 5.0.6 on 2024-05-27 12:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('criminology', '0002_category_subject_subject_code_questionnaire'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='questionnaire',
            unique_together={('subject', 'category')},
        ),
        migrations.RemoveField(
            model_name='questionnaire',
            name='subtopic',
        ),
        migrations.RemoveField(
            model_name='questionnaire',
            name='topic',
        ),
    ]