# Generated by Django 5.1 on 2024-09-30 01:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criminology', '0027_alter_students_studentid'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcademicYear',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('year_series', models.CharField(max_length=20)),
                ('period', models.CharField(max_length=200)),
                ('status', models.CharField(max_length=20)),
            ],
        ),
    ]
