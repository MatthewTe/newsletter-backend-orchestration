# Generated by Django 4.1.7 on 2023-03-12 22:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foreign_policy', '0003_foreginpolicyrssfeed_alter_articlelinks_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='foreginpolicyrssfeed',
            name='rss_feed_xml',
            field=models.FileField(blank=True, null=True, upload_to='foreign_policy/rss_feed/%Y/%m/%d'),
        ),
    ]
