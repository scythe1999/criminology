# Generated by Django 5.0.6 on 2024-05-27 02:59

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criminology', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='subject',
            name='subject_code',
            field=models.CharField(max_length=10, null=True),
        ),
        migrations.CreateModel(
            name='Questionnaire',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=600)),
                ('correct_answer', models.CharField(max_length=200)),
                ('distructor1', models.CharField(max_length=200)),
                ('distructor2', models.CharField(max_length=200)),
                ('distructor3', models.CharField(max_length=200)),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='criminology.category')),
                ('subject', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='criminology.subject')),
                ('subtopic', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='criminology.subtopic')),
                ('topic', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='criminology.topic')),
            ],
        ),
    ]