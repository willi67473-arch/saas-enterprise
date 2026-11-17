"""Migration initiale de l'app « projects » (générée à partir des modèles)."""
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tenants', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.ForeignKey('tenants.Tenant', editable=False, on_delete=models.CASCADE, related_name='+')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=50)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
                ('status', models.CharField(max_length=20, default='ACTIVE')),
                ('budget_hours', models.DecimalField(max_digits=8, decimal_places=2, default=0)),
                ('hourly_rate', models.DecimalField(max_digits=10, decimal_places=2, default=100)),
                ('deadline', models.DateField(null=True, blank=True)),
                ('owner', models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_projects')),
            ],
        ),
        migrations.AddConstraint(
            model_name='project',
            constraint=models.UniqueConstraint(fields=['tenant', 'code'], name='uniq_project_tenant_code'),
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tenant', models.ForeignKey('tenants.Tenant', editable=False, on_delete=models.CASCADE, related_name='+')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='tasks')),
                ('assignee', models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_tasks')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(null=True, blank=True)),
                ('column_status', models.CharField(max_length=20, default='TODO')),
                ('position', models.PositiveIntegerField(default=0)),
                ('priority', models.CharField(max_length=20, default='MEDIUM')),
                ('tags', models.JSONField(null=True, blank=True)),
                ('due_date', models.DateField(null=True, blank=True)),
            ],
        ),
        migrations.AddIndex(
            model_name='task',
            index=models.Index(fields=['project', 'column_status', 'position'], name='task_proj_col_pos_idx'),
        ),
    ]
