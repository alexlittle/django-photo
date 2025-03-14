from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('photo', '0010_alter_photoprops_value'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE photo_album ADD FULLTEXT INDEX album_fulltext_index (name, title, date_display);",
            "ALTER TABLE photo_album  DROP INDEX album_fulltext_index;",
        ),
        migrations.RunSQL(
            "ALTER TABLE photo_tag ADD FULLTEXT INDEX tag_fulltext_index (name, slug);",
            "ALTER TABLE photo_tag  DROP INDEX tag_fulltext_index;",
        ),
        migrations.RunSQL(
            "ALTER TABLE photo_photo ADD FULLTEXT INDEX photo_fulltext_index (file, title);",
            "ALTER TABLE photo_photo DROP INDEX photo_fulltext_index;",
        ),
    ]