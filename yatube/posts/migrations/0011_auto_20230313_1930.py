# Generated by Django 2.2.19 on 2023-03-13 19:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0010_auto_20230313_1924'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='follow',
            name='subscriber_author_uniqueness',
        ),
        migrations.RenameField(
            model_name='follow',
            old_name='following',
            new_name='author',
        ),
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('author', 'user'), name='subscriber_author_uniqueness'),
        ),
    ]
