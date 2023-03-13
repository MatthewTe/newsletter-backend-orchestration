# Generated by Django 4.1.7 on 2023-03-12 22:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foreign_policy', '0002_auto_20230312_0106'),
    ]

    operations = [
        migrations.CreateModel(
            name='ForeginPolicyRssFeed',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_extracted', models.DateTimeField(auto_now_add=True)),
                ('rss_feed_xml', models.FileField(null=True, upload_to='foreign_policy/rss_feed/%Y/%m/%d')),
            ],
        ),
        migrations.AlterField(
            model_name='articlelinks',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
