# Generated by Django 5.1 on 2024-09-05 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criminology', '0024_savedsubtopictable_subtopic_savedtopictable_topic'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreateStudents',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('lastname', models.CharField(max_length=200)),
                ('firstname', models.CharField(max_length=200)),
                ('studentid', models.CharField(max_length=200)),
                ('section', models.CharField(max_length=200)),
            ],
        ),
    ]
