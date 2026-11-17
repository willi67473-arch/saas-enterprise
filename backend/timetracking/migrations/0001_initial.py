"""Migration initiale de l'app « timetracking » (générée à partir des modèles)."""
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('projects', '0001_initial'),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.ForeignKey('tenants.Tenant', editable=False, on_delete=models.CASCADE, related_name='+')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='time_entries')),
                ('project', models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='time_entries')),
                ('task', models.ForeignKey('projects.Task', null=True, blank=True, on_delete=models.SET_NULL, related_name='time_entries')),
                ('description', models.CharField(max_length=255, null=True, blank=True)),
                ('started_at', models.DateTimeField()),
                ('ended_at', models.DateTimeField(null=True, blank=True)),
                ('duration_seconds', models.PositiveIntegerField(default=0)),
                ('is_billable', models.BooleanField(default=True)),
                ('is_running', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddConstraint(
            model_name='timeentry',
            constraint=models.UniqueConstraint(fields=['user'], condition=models.Q(is_running=True), name='uniq_running_timer_per_user'),
        ),
    ]
