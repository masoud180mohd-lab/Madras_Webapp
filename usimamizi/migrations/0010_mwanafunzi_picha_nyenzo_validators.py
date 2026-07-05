# Generated manually for student photos and material upload validation.

from django.db import migrations, models
import usimamizi.models


class Migration(migrations.Migration):

    dependencies = [
        ('usimamizi', '0009_msetomtihani_alter_ainamalipo_id_alter_darasa_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mwanafunzi',
            name='picha',
            field=models.ImageField(blank=True, null=True, upload_to='picha_za_wanafunzi/', validators=[usimamizi.models.validate_picha]),
        ),
        migrations.AlterField(
            model_name='nyenzo',
            name='faili',
            field=models.FileField(upload_to='nyenzo_masomo/', validators=[usimamizi.models.validate_nyenzo]),
        ),
    ]
