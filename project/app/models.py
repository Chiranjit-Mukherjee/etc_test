from __future__ import unicode_literals
from django.db import models
from django.contrib.auth.models import User
import os
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from datetime import date, timedelta


#@receiver(post_save, sender=<model_name>)
#def create_log(sender, instance, **kwargs):
#	pass






class user_profile(models.Model):
	user = models.OneToOneField(User, related_name='user')
	first_name = models.CharField(max_length=50, blank=True, null=True)
	last_name = models.CharField(max_length=50, blank=True, null=True)
	user_type = models.CharField(max_length=50, blank=True, null=True)	
	

	def __unicode__(self):
		return str(self.user)


def file_upload_function(instance, filename):
	return os.path.join('files/%s/' % instance.result_id, filename)



	

def upload_head_file(instance, filename):

	filename = 'hd'+str(instance.result_id)

	return os.path.join('files/%s/' % instance.result_id, filename)


def upload_body_file(instance, filename):
	filename = 'bd'+str(instance.result_id)

	return os.path.join('files/%s/' % instance.result_id, filename)
	

def upload_footer_file(instance, filename):

	filename = 'ft'+str(instance.result_id)

	return os.path.join('files/%s/' % instance.result_id, filename)


# result convert information
class rc_info(models.Model):
	# exam_id
	result_id = models.IntegerField(blank=True, null=True, unique=True)   

	replicated_from = models.CharField(max_length=20, blank=True, null=True)

	# stored data file_name
	main_file = models.FileField(blank=True, null=True, upload_to=file_upload_function)
	main_line_terminator = models.CharField(max_length=20, blank=True, null=True)

	#========================== For Multi file ==============================
	
	# file for header section
	head_file = models.FileField(blank=True, null=True, upload_to=upload_head_file)
	head_primary_field = models.CharField(max_length=250, blank=True, null=True)
	head_line_terminator = models.CharField(max_length=20, blank=True, null=True)

	head_prompt = models.TextField(blank=True, null=True)

	# file for body section
	body_file = models.FileField(blank=True, null=True, upload_to=upload_body_file)
	body_primary_field = models.CharField(max_length=250, blank=True, null=True)
	body_line_terminator = models.CharField(max_length=20, blank=True, null=True)
	
	body_prompt = models.TextField(blank=True, null=True)



	# file for footer section
	footer_file = models.FileField(blank=True, null=True, upload_to=upload_footer_file)
	footer_primary_field = models.CharField(max_length=250, blank=True, null=True)
	foot_line_terminator = models.CharField(max_length=20, blank=True, null=True)

	footer_prompt = models.TextField(blank=True, null=True)


	#=========================================================================


	#original data file name
	org_file_name = models.CharField(max_length=300, blank=True, null=True)
	# datafile separator
	separator = models.CharField(max_length=50, blank=True, null=True)  # ',' / '|' / ':'


	# has header yes / no
	header = models.BooleanField(default=True)    # Yes / No
	# original header file name
	org_header_file_name = models.CharField(max_length=300, blank=True, null=True)
	# stored header file
	header_file = models.FileField(blank=True, null=True, upload_to='media/files/')
	# header separator
	header_separator = models.CharField(max_length=10, blank=True, null=True)		
	

	# actual created table name
	table_name = models.CharField(max_length=50, blank=True, null=True)		# cr+result_id
	# no of rows in data file
	no_of_rows = models.IntegerField(blank=True, null=True)
	# no of columns in data file
	no_of_columns = models.IntegerField(blank=True, null=True)

	no_of_files_uploaded = models.IntegerField(blank=True, null=True)


	# automatically generated
	database_columns = models.CharField(max_length=300, blank=True, null=True) # c1|c2||||cn
	# original column name from header file
	original_columns = models.TextField(blank=True, null=True) 	# fields from header file
	# edited column names, edited by operator
	innova_columns = models.TextField(blank=True, null=True)    # fields edited by user

	# fields that has auto prompt
	auto_prompt = models.TextField(blank=True, null=True)

	
	# code colimns present yes / no 
	code_column_present = models.BooleanField(default=False)
	code_column_text = models.TextField(blank=True, null=True) # c1,c2|c3,c4|
	code_column_row_separator = models.CharField(max_length=10, blank=True, null=True)  # '|' / '\n'
	code_column_field_separator = models.CharField(max_length=10, blank=True, null=True) # ','
	
	code_columns = models.CharField(max_length=300, blank=True, null=True)  # can be many field

	

	# columns will be indexed
	search_columns = models.CharField(max_length=300, blank=True, null=True)  	# c1|c2||||cn

	# choose by operator
	header_columns = models.CharField(max_length=300, blank=True, null=True)	# c1|c2||||cn

	# choose by operator
	body_columns = models.CharField(max_length=300, blank=True, null=True)		# c1|c2||||cn

	# choose by operator
	footer_columns = models.CharField(max_length=300, blank=True, null=True)	# c1|c2||||cn
	


	uploaded_file_format = models.CharField(max_length=10, blank=True, null=True)  #txt / xls / xlsx / csv
	created_on = models.DateField(auto_now_add=True)

	finalized = models.BooleanField(default=False)
	finalized_on = models.DateField(blank=True, null=True)
	finalized_by = models.ForeignKey(user_profile, related_name="finalized_by")


	def __unicode__(self):
		return str(self.result_id)



# to map cell no to field value
class cell_mapping(models.Model):
	for_record = models.ForeignKey(rc_info, related_name="for_record")
	key = models.CharField(max_length=50, blank=True, null=True) # final cell no from data table
	value = models.CharField(max_length=300, blank=True, null=True) # value on that cell
	field_type = models.CharField(max_length=50, blank=True, null=True) # header / body / footer

	def __unicode__(self):
		return str(self.for_record)



# class replicate_records(models.Model):
# 	replicated_record = models.ForeignKey(rc_info, related_name="replicated_record")
# 	new_record = models.ForeignKey(rc_info, related_name="new_record")
# 	created_by = models.ForeignKey(user_profile, related_name="created_by")	
# 	created_on = models.DateField(auto_now_add=True)

# 	def __unicode__(self):
# 		return str(self.replicated_record)