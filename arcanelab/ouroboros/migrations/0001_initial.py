# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-19 00:59
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import arcanelab.ouroboros.fields
import arcanelab.ouroboros.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='CourseInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='Date and time of record creation', verbose_name='Creation Date')),
                ('updated_on', models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='Date and time of last record update', verbose_name='Update Date')),
                ('term_level', models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CourseSpec',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(blank=True, help_text='Internal (unique) code', max_length=20, verbose_name='Code')),
                ('name', models.CharField(max_length=60, verbose_name='Name')),
                ('description', models.TextField(max_length=1023, verbose_name='Description')),
                ('cancel_permission', models.CharField(blank=True, help_text='Permission code (as <application>.<permission>) to test against when this course instance is cancelled. The user who intends to cancel this course instance must satisfy this permission against the associated document.', max_length=201, null=True, verbose_name='Cancel Permission')),
            ],
            options={
                'verbose_name': 'Course Spec',
                'verbose_name_plural': 'Course Specs',
            },
        ),
        migrations.CreateModel(
            name='NodeInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='Date and time of record creation', verbose_name='Creation Date')),
                ('updated_on', models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='Date and time of last record update', verbose_name='Update Date')),
                ('course_instance', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='node_instance', to='ouroboros.CourseInstance')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NodeSpec',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('enter', 'Enter'), ('exit', 'Exit'), ('cancel', 'Cancel'),
                                                   ('joined', 'Joined'), ('input', 'Input'), ('step', 'Step'),
                                                   ('multiplexer', 'Multiplexer'), ('split', 'Split')],
                                          help_text='Node type', max_length=15, verbose_name='Type')),
                ('code', models.SlugField(help_text='Internal (unique) code', max_length=20, verbose_name='Code')),
                ('name', models.CharField(max_length=60, verbose_name='Name')),
                ('description', models.TextField(max_length=1023, verbose_name='Description')),
                ('landing_handler', arcanelab.ouroboros.fields.CallableReferenceField(blank=True, help_text='A callable that will triggered when this node is reached. The expected signature is (document, user) since no interaction is expected to exist with the workflow instance, but the handlers should perform actions in the document', max_length=255, null=True, verbose_name='Landing Handler')),
                ('exit_value', models.PositiveSmallIntegerField(blank=True, help_text='Exit value. Expected only for exit nodes', null=True, verbose_name='Exit Value')),
                ('joiner', arcanelab.ouroboros.fields.CallableReferenceField(blank=True, help_text="A callable that will be triggered every time a split's branch reaches an end. The split's branch will trigger this callable which must return a valid transition name (existing action as outbound in this node) to leave the split and take an action, or None to remain in the split and wait for other branches (an exception will be raised if None is returned but no branch is still to finish). Its contract is (document, statuses, last) being the associated document, a dictionary of branch codes and their exit values (None: running; -1: cancelled or joined,>= 0: terminated by exit node), and the code of the branch being joined (such code will be present in the dictionary)", max_length=255, null=True, verbose_name='Joiner')),
                ('execute_permission', models.CharField(blank=True, help_text='Permission code (as <application>.<permission>) to test against when an action on this node is executed. The user who intends to execute the action in this node must satisfy this permission against the associated document', max_length=201, null=True, verbose_name='Cancel Permission')),
                ('branches', models.ManyToManyField(blank=True, help_text='Courses this node branches to. Expected only for split nodes', related_name='callers', to='ouroboros.CourseSpec', verbose_name='Branches')),
                ('course_spec', models.ForeignKey(help_text='Course spec this node spec belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='node_specs', to='ouroboros.CourseSpec', verbose_name='Course Spec')),
            ],
            options={
                'verbose_name': 'Node',
                'verbose_name_plural': 'Nodes',
            },
        ),
        migrations.CreateModel(
            name='TransitionSpec',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_name', models.SlugField(blank=True, help_text='Action name for this transition. Unique with respect to the origin node. Expected only for split and input nodes', max_length=20, null=True, verbose_name='Action Name')),
                ('name', models.CharField(max_length=60, verbose_name='Name')),
                ('description', models.TextField(max_length=1023, verbose_name='Description')),
                ('permission', models.CharField(blank=True, help_text='Permission code (as <application>.<permission>) to test against. It is not required, but only allowed if coming from an input node', max_length=201, null=True, verbose_name='Permission')),
                ('condition', arcanelab.ouroboros.fields.CallableReferenceField(blank=True, help_text='A callable evaluating the condition. Expected only for multiplexer nodes. The condition will evaluate with signature (document, user) and will return a value that will be treated as boolean.', max_length=255, null=True, verbose_name='Condition')),
                ('priority', models.PositiveSmallIntegerField(blank=True, help_text='A priority value used to order evaluation of condition. Expected only for multiplexer nodes', null=True, verbose_name='Priority')),
                ('destination', models.ForeignKey(help_text='Destination node', on_delete=django.db.models.deletion.CASCADE, related_name='inbounds', to='ouroboros.NodeSpec', validators=[arcanelab.ouroboros.models.valid_destination_types], verbose_name='Destination')),
                ('origin', models.ForeignKey(help_text='Origin node', on_delete=django.db.models.deletion.CASCADE, related_name='outbounds', to='ouroboros.NodeSpec', validators=[arcanelab.ouroboros.models.valid_origin_types], verbose_name='Origin')),
            ],
            options={
                'verbose_name': 'Transition Spec',
                'verbose_name_plural': 'Transition Specs',
            },
        ),
        migrations.CreateModel(
            name='WorkflowInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='Date and time of record creation', verbose_name='Creation Date')),
                ('updated_on', models.DateTimeField(default=django.utils.timezone.now, editable=False, help_text='Date and time of last record update', verbose_name='Update Date')),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Workflow Instance',
                'verbose_name_plural': 'Workflow Instances',
            },
        ),
        migrations.CreateModel(
            name='WorkflowSpec',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.SlugField(help_text='Internal (unique) code', max_length=20, unique=True, verbose_name='Code')),
                ('name', models.CharField(max_length=60, verbose_name='Name')),
                ('description', models.TextField(max_length=1023, verbose_name='Description')),
                ('create_permission', models.CharField(blank=True, help_text='Permission code (as <application>.<permission>) to test against when a workflow instance is created. The user who intends to create a workflow instance must satisfy this permission against the associated document.', max_length=201, null=True, verbose_name='Create Permission')),
                ('cancel_permission', models.CharField(blank=True, help_text='Permission code (as <application>.<permission>) to test against when a course instance is cancelled. The user who intends to cancel a course instance in this workflow must satisfy this permission against the associated document.', max_length=201, null=True, verbose_name='Cancel Permission')),
                ('document_type', models.ForeignKey(help_text='Accepted related document class', on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType', validators=[arcanelab.ouroboros.models.valid_document_type], verbose_name='Document Type')),
            ],
            options={
                'verbose_name': 'Workflow Spec',
                'verbose_name_plural': 'Workflow Specs',
            },
        ),
        migrations.AddField(
            model_name='workflowinstance',
            name='workflow_spec',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='ouroboros.WorkflowSpec'),
        ),
        migrations.AddField(
            model_name='nodeinstance',
            name='node_spec',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='ouroboros.NodeSpec'),
        ),
        migrations.AddField(
            model_name='coursespec',
            name='workflow_spec',
            field=models.ForeignKey(help_text='Workflow spec this course spec belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='course_specs', to='ouroboros.WorkflowSpec', verbose_name='Workflow Spec'),
        ),
        migrations.AddField(
            model_name='courseinstance',
            name='course_spec',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ouroboros.CourseSpec'),
        ),
        migrations.AddField(
            model_name='courseinstance',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='branches', to='ouroboros.NodeInstance'),
        ),
        migrations.AddField(
            model_name='courseinstance',
            name='workflow_instance',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='courses', to='ouroboros.WorkflowInstance'),
        ),
        migrations.AlterUniqueTogether(
            name='workflowinstance',
            unique_together={('content_type', 'object_id')},
        ),
        migrations.AlterUniqueTogether(
            name='nodespec',
            unique_together={('course_spec', 'code')},
        ),
        migrations.AlterUniqueTogether(
            name='coursespec',
            unique_together={('workflow_spec', 'code')},
        ),
    ]
