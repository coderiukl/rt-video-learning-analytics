import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analytics", "0001_initial"),
        ("courses", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LearningSession",
            fields=[
                ("session_id", models.CharField(max_length=64, primary_key=True, serialize=False)),
                ("started_at", models.DateTimeField()),
                ("ended_at", models.DateTimeField(blank=True, null=True)),
                ("active_seconds", models.PositiveIntegerField(default=0)),
                ("idle_seconds", models.PositiveIntegerField(default=0)),
                ("event_count", models.PositiveIntegerField(default=0)),
                ("device_type", models.CharField(blank=True, max_length=40)),
                ("browser", models.CharField(blank=True, max_length=80)),
                ("user_agent", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("course", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="learning_sessions", to="courses.course")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="learning_sessions", to="users.studentprofile")),
            ],
            options={
                "db_table": "learning_sessions",
                "ordering": ["-started_at"],
                "indexes": [
                    models.Index(fields=["student", "course"], name="learning_se_student_56f780_idx"),
                    models.Index(fields=["course", "started_at"], name="learning_se_course__67c29d_idx"),
                ],
            },
        ),
        migrations.AddField("learningevent", "client_timestamp", models.DateTimeField(blank=True, null=True)),
        migrations.AddField("learningevent", "duration_ms", models.PositiveIntegerField(default=0)),
        migrations.AddField("learningevent", "is_fullscreen", models.BooleanField(default=False)),
        migrations.AddField("learningevent", "is_tab_hidden", models.BooleanField(default=False)),
        migrations.AddField("learningevent", "muted", models.BooleanField(default=False)),
        migrations.AddField("learningevent", "volume", models.FloatField(blank=True, null=True)),
        migrations.AddField(
            "learningevent",
            "session",
            models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="events", to="analytics.learningsession"),
        ),
    ]
