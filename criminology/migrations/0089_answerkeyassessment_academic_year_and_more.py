# Generated by Django 5.1.3 on 2024-11-26 05:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('criminology', '0088_alter_studentsscoreassessment_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='answerkeyassessment',
            name='academic_year',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='criminology.academicyear'),
        ),
        migrations.AddField(
            model_name='answerkeytableofspecification',
            name='academic_year',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='criminology.academicyear'),
        ),
    ]
