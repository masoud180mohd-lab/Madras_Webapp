from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usimamizi", "0018_whatsapp_call_log_choices"),
    ]

    operations = [
        migrations.AlterField(
            model_name="rekodiukaguzi",
            name="kitendo",
            field=models.CharField(
                choices=[
                    ("mahudhurio_kawaida", "Mahudhurio (kawaida)"),
                    ("mahudhurio_hifdhu", "Mahudhurio (hifdhu)"),
                    ("malipo", "Malipo"),
                    ("hamisha_darasa", "Hamisha darasa"),
                ],
                db_index=True,
                max_length=40,
            ),
        ),
    ]
