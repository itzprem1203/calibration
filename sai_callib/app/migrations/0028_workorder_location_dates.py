from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0027_widen_customer_gst_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='workorder',
            name='location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='workorder',
            name='calibration_date',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='workorder',
            name='next_due_date',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
