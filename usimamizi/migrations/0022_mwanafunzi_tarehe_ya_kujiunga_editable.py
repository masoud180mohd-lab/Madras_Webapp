from datetime import date

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usimamizi", "0021_aina_malipo_mwaka_mwezi"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mwanafunzi",
            name="tarehe_ya_kujiunga",
            field=models.DateField(
                default=date.today,
                help_text="Tarehe aliyosajiliwa kwenye madrasa.",
                verbose_name="Tarehe ya kujiunga",
            ),
        ),
    ]
