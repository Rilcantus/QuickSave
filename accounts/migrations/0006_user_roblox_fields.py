from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_user_psn_account_id_user_psn_avatar_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='roblox_username',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='roblox_user_id',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='user',
            name='roblox_avatar',
            field=models.URLField(blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='roblox_polling_enabled',
            field=models.BooleanField(default=False),
        ),
    ]
