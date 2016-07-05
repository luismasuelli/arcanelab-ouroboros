# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-05 03:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import grimoire.django.flowkeeper.fields
import grimoire.django.flowkeeper.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(help_text='Internal (unique) code', max_length=20, verbose_name='Code')),
                ('depth', models.PositiveSmallIntegerField(help_text='Tells the depth of this course. The main course must be of depth 0, while successive descendants should increment the level by 1', verbose_name='Depth')),
            ],
            options={
                'verbose_name': 'Course',
                'verbose_name_plural': 'Courses',
            },
        ),
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(help_text='Node type', max_length=15, verbose_name='Type')),
                ('code', models.SlugField(help_text='Internal (unique) code', max_length=20, verbose_name='Code')),
                ('exit_value', models.PositiveSmallIntegerField(blank=True, help_text='Exit value. Expected only for exit nodes', null=True, verbose_name='Exit Value')),
                ('joiner', grimoire.django.flowkeeper.fields.CallableReferenceField(blank=True, help_text='A callable that will be triggered every time a joined branch reaches an end. The joined branch will trigger this callable also providing the exit value (which is a positive integer, or -1 if the branch was closed due to a cancelation node). This callable must return a valid transition name (existing outbound in this node) to leave the split and take an action, or None to remain in the split and wait for other branches (an exception will be raised if None is returned but no branch is still to finish)', max_length=255, null=True, verbose_name='Joiner')),
                ('branches', models.ManyToManyField(blank=True, help_text='Courses this node branches to. Expected only for split nodes', related_name='callers', to='flowkeeper.Course', verbose_name='Branches')),
                ('course', models.ForeignKey(help_text='Course this node belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='nodes', to='flowkeeper.Course', verbose_name='Course')),
            ],
            options={
                'verbose_name': 'Node',
                'verbose_name_plural': 'Nodes',
            },
        ),
        migrations.CreateModel(
            name='Transition',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_name', models.SlugField(blank=True, help_text='Action name for this transition. Unique with respect to the origin node. Expected only for split and input nodes', max_length=30, null=True, verbose_name='Action Name')),
                ('permission', models.CharField(blank=True, help_text='Permission code (as <application>.<permission>) to test against. It is not required, but only allowed if coming from an input node.', max_length=201, null=True, verbose_name='Permission')),
                ('condition', grimoire.django.flowkeeper.fields.CallableReferenceField(blank=True, help_text='A callable evaluating the condition. Expected only for multiplexer nodes', max_length=255, null=True, verbose_name='Condition')),
                ('priority', models.PositiveSmallIntegerField(blank=True, help_text='A priority value used to order evaluation of condition. Expected only for multiplexer nodes', null=True, verbose_name='Priority')),
                ('destination', models.ForeignKey(help_text='Destination node', on_delete=django.db.models.deletion.CASCADE, related_name='inbounds', to='flowkeeper.Node', validators=[grimoire.django.flowkeeper.models.valid_destination_types], verbose_name='Destination')),
                ('origin', models.ForeignKey(help_text='Origin node', on_delete=django.db.models.deletion.CASCADE, related_name='outbounds', to='flowkeeper.Node', validators=[grimoire.django.flowkeeper.models.valid_origin_types], verbose_name='Origin')),
            ],
            options={
                'verbose_name': 'Transition',
                'verbose_name_plural': 'Transitions',
            },
        ),
        migrations.CreateModel(
            name='Workflow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(help_text='Internal (unique) code', max_length=20, unique=True, verbose_name='Code')),
                ('name', models.CharField(max_length=60, verbose_name='Name')),
                ('description', models.CharField(max_length=100, verbose_name='Description')),
                ('permission', models.CharField(blank=True, help_text='Permission code (as <application>.<permission>) to test against. The user who intends to create a workflow instance must satisfy this permission.', max_length=201, null=True, verbose_name='Permission')),
                ('document_type', models.ForeignKey(help_text='Accepted related document class', on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType', validators=[grimoire.django.flowkeeper.models.valid_document_type], verbose_name='Document Type')),
            ],
            options={
                'verbose_name': 'Workflow',
                'verbose_name_plural': 'Workflows',
            },
        ),
        migrations.AddField(
            model_name='course',
            name='workflow',
            field=models.ForeignKey(help_text='Workflow this course belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='flowkeeper.Workflow', verbose_name='Workflow'),
        ),
        migrations.AlterUniqueTogether(
            name='node',
            unique_together=set([('course', 'code')]),
        ),
        migrations.AlterUniqueTogether(
            name='course',
            unique_together=set([('workflow', 'code')]),
        ),
    ]
