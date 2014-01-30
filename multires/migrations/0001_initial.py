# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MultiresRecipe'
        db.create_table(u'multires_multiresrecipe', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=256, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('namespace', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('automatic', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('ad_hoc', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('flip', self.gf('django.db.models.fields.CharField')(default=u'', max_length=4, blank=True)),
            ('rotate', self.gf('django.db.models.fields.SmallIntegerField')(null=True, blank=True)),
            ('rotate_crop', self.gf('django.db.models.fields.CharField')(default=u'', max_length=16, blank=True)),
            ('rotate_color', self.gf('django_auxilium.models.fields.multiple_values.MultipleValuesField')(blank=True, max_values=4, max_length=16, min_values=4)),
            ('crop', self.gf('django_auxilium.models.fields.multiple_values.MultipleValuesField')(blank=True, max_values=4, max_length=32, min_values=4)),
            ('width', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('height', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('upscale', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('fit', self.gf('django.db.models.fields.CharField')(default=u'fit', max_length=8)),
            ('file_type', self.gf('django.db.models.fields.CharField')(default=u'jpeg', max_length=4)),
            ('quality', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'multires', ['MultiresRecipe'])

        # Adding unique constraint on 'MultiresRecipe', fields ['namespace', 'title']
        db.create_unique(u'multires_multiresrecipe', ['namespace', 'title'])

        # Adding model 'MultiresImage'
        db.create_table(u'multires_multiresimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(unique=True, max_length=32, blank=True)),
            ('source', self.gf('multires.fields.SourceImageField')(max_length=100, db_index=True)),
            ('recipe', self.gf('django.db.models.fields.related.ForeignKey')(related_name=u'images', to=orm['multires.MultiresRecipe'])),
            ('processed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('image', self.gf('multires.fields.LazyMultiresImageField')(max_length=100, upload_to=u'multires/images/', blank=True)),
            ('width', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('height', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
            ('size', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'multires', ['MultiresImage'])

        # Adding unique constraint on 'MultiresImage', fields ['source', 'recipe']
        db.create_unique(u'multires_multiresimage', ['source', 'recipe_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'MultiresImage', fields ['source', 'recipe']
        db.delete_unique(u'multires_multiresimage', ['source', 'recipe_id'])

        # Removing unique constraint on 'MultiresRecipe', fields ['namespace', 'title']
        db.delete_unique(u'multires_multiresrecipe', ['namespace', 'title'])

        # Deleting model 'MultiresRecipe'
        db.delete_table(u'multires_multiresrecipe')

        # Deleting model 'MultiresImage'
        db.delete_table(u'multires_multiresimage')


    models = {
        u'multires.multiresimage': {
            'Meta': {'unique_together': "((u'source', u'recipe'),)", 'object_name': 'MultiresImage'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('multires.fields.LazyMultiresImageField', [], {'max_length': '100', u'upload_to': "u'multires/images/'", 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recipe': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'images'", 'to': u"orm['multires.MultiresRecipe']"}),
            'size': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source': ('multires.fields.SourceImageField', [], {'max_length': '100', 'db_index': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'blank': 'True'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'multires.multiresrecipe': {
            'Meta': {'unique_together': "((u'namespace', u'title'),)", 'object_name': 'MultiresRecipe'},
            'ad_hoc': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'automatic': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'crop': ('django_auxilium.models.fields.multiple_values.MultipleValuesField', [], {'blank': 'True', u'max_values': '4', 'max_length': '32', u'min_values': '4'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'file_type': ('django.db.models.fields.CharField', [], {'default': "u'jpeg'", 'max_length': '4'}),
            'fit': ('django.db.models.fields.CharField', [], {'default': "u'fit'", 'max_length': '8'}),
            'flip': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '4', 'blank': 'True'}),
            'height': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'namespace': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'quality': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rotate': ('django.db.models.fields.SmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rotate_color': ('django_auxilium.models.fields.multiple_values.MultipleValuesField', [], {'blank': 'True', u'max_values': '4', 'max_length': '16', u'min_values': '4'}),
            'rotate_crop': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '16', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'upscale': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'width': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        }
    }

    complete_apps = ['multires']