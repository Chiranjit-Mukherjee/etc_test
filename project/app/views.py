#from django.shortcuts import render
#from django.contrib.auth.models import User
from app.models import *
from app.forms import *
# from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.db import connection
import time

import pyexcel as pex 
import unicodedata

from django.conf import settings


#import re
from random import randint
#from django.core import serializers
#from django.core.mail import EmailMessage
#from django.db.models import Max, Count, Sum, F, Q
#from datetime import datetime
#from django.views.decorators.csrf import csrf_exempt
# =============
#from datetime import date, timedelta
#from datetime import datetime
#import json

#================== Error Pages ==========================
def error_404(request):
	
	return render(request, 'error_pages/error_404.html', {})

def error_500(request):
	return render(request, 'error_pages/error_500.html', {})
	

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ==========================================================



def home(request):
	if request.user.is_authenticated():
		return redirect('/dashboard/')

	else:
		return redirect('/user_login/')


def user_login(request):
	if request.method == 'POST':


		# IP White List Checking
		ip_address = get_client_ip(request)

		allowed_ip_addresses = ('10.0.1.25', '10.0.1.20', '127.0.0.1', '10.0.1.14')

		if not ip_address in allowed_ip_addresses:
			return JsonResponse({'status':0, 'message':'You are not allowed to access this site.\n Your IP Address : '+ip_address})

		

		if not 'username' in request.POST.keys()  or 'password' not in request.POST.keys() \
							or 'captcha' not in request.POST.keys():

			return JsonResponse({'status':0, 'message':'Invalid Request Sent'})

		captcha = request.session['captcha']

		if captcha != request.POST['captcha']:
			return JsonResponse({'status':2, 'message':'Captcha Did Not Match Please Try Again'})


		username = request.POST['username']
		password = request.POST['password']

		if not User.objects.filter(username=username).exists():
			return JsonResponse({'status':0,'message':"Such User Doesn't Exist"})

		user = authenticate(username=username, password=password)

		if user:
			login(request, user)
			del request.session['captcha']

			return JsonResponse({'status':1, 'message':'Login Successful'})
				
		else:
			return JsonResponse({'status':0, 'message':'Invalid Credentials Provided'})

	else:
		captcha = str(randint(1000, 9999))

		request.session['captcha'] = captcha

		return render(request, 'login.html', {'captcha':captcha})



@login_required
def user_logout(request):
	logout(request)
	return redirect('/')




@login_required
def dashboard(request):
	return render(request, 'dashboard.html', {})


#================================== Parameter Part =======================================


# ---------- Replication Part ---------------#
@login_required
def replicate_record(request):
	if request.method == 'POST':

		if not 'old_exam_id' in request.POST.keys() or request.POST['old_exam_id'] =='':
			return JsonResponse({'status':0, 'message':'Please Give Old Exam Id'})

		if not 'new_exam_id' in request.POST.keys() or request.POST['new_exam_id'] =='':
			return JsonResponse({'status':0, 'message':'Please Give New Exam Id'})

		old_exam_id = request.POST['old_exam_id']

		new_exam_id = request.POST['new_exam_id']

		if not rc_info.objects.filter(result_id=old_exam_id).exists():
			return JsonResponse({'status':0, 'message':'You have specified a wrong old exam id. No such record exists'})

		if rc_info.objects.filter(result_id=new_exam_id).exists():
			return JsonResponse({'status':0, 'message':'You have specified a wrong new exam id. A record with this exam id already exists'})

		#===================== Creting Clone of Old Record ===================#

		new_record = rc_info.objects.get(result_id=old_exam_id)
		old_record = rc_info.objects.get(result_id=old_exam_id)
			

		new_record.pk = None		

		new_record.result_id = new_exam_id
		
		new_record.replicated_from = old_record.result_id

		new_record.save()


		# replicate_records.objects.create(replicated_record=old_record, new_record=new_record, created_by=request.user.user)


		if cell_mapping.objects.filter(for_record=new_record).exists():
			cell_mapping.objects.filter(for_record=new_record).delete()

		# Creting the copy of design
		if cell_mapping.objects.filter(for_record=old_record).exists():
			old_design = cell_mapping.objects.filter(for_record=old_record)

			for i in old_design:
				cell_mapping.objects.create(for_record=new_record, key=i.key, value=i.value, field_type=i.field_type)

		#==================== Record Cloning Ends Here ======================#

		return JsonResponse({'status':1, 'new_record_id':new_record.id})


	else:
		return render(request, 'replicate.html', {})



@login_required
def old_parameter(request, record_id):
	
	new_record = rc_info.objects.get(id=record_id)

	old_record = rc_info.objects.get(result_id=new_record.replicated_from)


	return render(request, 'old_parameter.html', {'no_of_files':new_record.no_of_files_uploaded,\
					 'old_exam_id':old_record.result_id, 'new_exam_id':new_record.result_id, 'new_record_id':new_record.id })



#------------------------------------------#


@login_required
def data_management(request):
	if request.method == 'POST':

		if not 'exam_id' in request.POST.keys():
			return JsonResponse({"status":0, 'message':"Invalid Request Sent"})

		exam_id = request.POST['exam_id']

		if len(request.POST['exam_id']) != 5:
			return JsonResponse({"status":0, 'message':"Exam ID Must be of five digits"})

		if not exam_id.isdigit():
			return JsonResponse({'status':0, 'message':'Please Give Only Positive Number As Exam ID'})

		if rc_info.objects.filter(result_id=exam_id).exists():
			get_record = rc_info.objects.get(result_id=exam_id)

			if get_record.finalized:
				return JsonResponse({'status':2, 'message':'This id is already finalized you can not modify this.'})

			else:
				return JsonResponse({'status':3, 'message':'This Exam ID Already Exists'})

		# create_record = rc_info.objects.create(result_id=exam_id, finalized_by=request.user.user)

		return JsonResponse({'status':1, 'message':'Success'})

	return render(request, 'datamanagement.html', {})





@login_required
def take_parameter(request, record_id):
	
	if rc_info.objects.filter(result_id=record_id).exists():
		get_record = rc_info.objects.get(result_id=record_id)	

	else:
		get_record = rc_info.objects.create(result_id=record_id, finalized_by=request.user.user)


	finalized = get_record.finalized

	report = ''

	if finalized:
		

		report = '<label> File Type : '+str(get_record.uploaded_file_format)+' </label><p></p>'+\
				'<label> No of Files Uploaded : '+str(get_record.no_of_files_uploaded)+' </label><p></p>'

		if get_record.no_of_files_uploaded == 1:
			report = report+'<label> File Name : '+str(get_record.main_file)+' </label><p></p>'

		else:
			report = report+'<label>Head Section File Name : '+str(get_record.head_file)+' </label><p></p>'+\
							'<label>Body Section File Name : '+str(get_record.body_file)+' </label><p></p>'+\
							'<label>Footer Section File Name : '+str(get_record.footer_file)+' </label><p></p>'



		report = report+'<label> Code Column Present : '+str(get_record.code_column_present)+' </label><p></p>'

	
	return render(request, 'take_parameter.html', {'record':get_record, 'finalized':finalized, 'report':report,\
													 'record_id':get_record.id})





@login_required
def process_parameter(request):
	if request.method == 'POST':

		result_id = request.POST['result_id']

		#============== Validation Checking =================

		if not rc_info.objects.filter(result_id=result_id).exists():
			return JsonResponse({'status':0, 'message':'Invalid Request Sent'})

		get_record = rc_info.objects.get(result_id=result_id)
		
		get_record.no_of_files_uploaded = len(request.FILES.keys())

		get_record.save()

		print request.FILES.keys()


		if not 'main_file' in request.FILES.keys() and not 'header_file' in request.FILES.keys() and\
		 		not 'body_file' in request.FILES.keys() and not 'footer_file' in request.FILES.keys():
			return JsonResponse({'status':0, 'message':'Please Upload your data File'})



		if request.POST['header'] == 'No' and request.FILES['col_header_file'] == '':
			return JsonResponse({'status':0, 'message':'Please upload your header file'})


		if request.POST['code_field'] == 'Yes':

			if request.POST['code_field_text'] == '':
				return JsonResponse({'status':0, 'message':'You can not leave code column text blank'})

			if request.POST['code_field_row_separator'] == '':
				return JsonResponse({'status':0, 'message':'You can not leave code column row separator blank'})

			if request.POST['code_field_col_separator'] == '':
				return JsonResponse({'status':0, 'message':'You can not leave code column column separator blank'})

		#======================================================

		if request.POST['separator'] == 'Comma':
			get_record.separator = ','

		elif request.POST['separator'] == 'Colon':
			get_record.separator = ':'

		else:
			get_record.separator = '|'


		# storing primary field value
		if 'head_primary' in request.POST.keys():
			get_record.head_primary_field = request.POST['head_primary']

		if 'body_primary' in request.POST.keys():
			get_record.body_primary_field = request.POST['body_primary']

		if 'footer_primary' in request.POST.keys():
			get_record.footer_primary_field = request.POST['footer_primary']
	



		if 'main_file' in request.FILES.keys():
			get_record.main_file = request.FILES['main_file']

		if 'header_file' in request.FILES.keys():
			get_record.head_file = request.FILES['header_file']

		if 'body_file' in request.FILES.keys():
			get_record.body_file = request.FILES['body_file']
			


		if 'footer_file' in request.FILES.keys():
			get_record.footer_file = request.FILES['footer_file']
			



		if 'extra_info' in request.POST.keys() and request.POST['extra_info'] != '':

			if request.POST['extra_info'] == 'HB':

				
				get_record.body_file = get_record.head_file

				# get_record.body_primary_field = get_record.head_primary_field


			elif request.POST['extra_info'] == 'HF':

				get_record.footer_file = get_record.head_file

				# get_record.footer_primary_field = get_record.head_primary_field

			elif request.POST['extra_info'] == 'FB':

				get_record.body_file = get_record.footer_file

				# get_record.footer_primary_field = get_record.body_primary_field




			

		get_record.save()


		#================== Checking that primary field's existence ================

		if get_record.head_file != None and get_record.head_file != '':
			filename = "./media/"+str(get_record.head_file)

			with open(filename) as file:
				line = file.readline()

			line = line.split(get_record.separator)

			print line

			if not str(get_record.head_primary_field) in line:
				return JsonResponse({'status':0, 'message':'The Header Section File Does Not Contain The Specifeid PRIMARY KEY'})



		if get_record.body_file != None and get_record.body_file != '':
			filename = "./media/"+str(get_record.body_file)

			with open(filename) as file:
				line = file.readline()

			line = line.split(get_record.separator)

			if not str(get_record.body_primary_field) in line:
				return JsonResponse({'status':0, 'message':'The Body Section File Does Not Contain The Specifeid PRIMARY KEY'})
				


		if get_record.footer_file != None and get_record.footer_file != '':
			filename = "./media/"+str(get_record.footer_file)

			with open(filename) as file:
				line = file.readline()

			line = line.split(get_record.separator)

			if not str(get_record.footer_primary_field) in line:
				return JsonResponse({'status':0, 'message':'The Footer Section File Does Not Contain The Specifeid PRIMARY KEY'})
				


		#=============== Primary Fields existence checking done ========================


		



		if request.POST['header'] == 'No':
			get_record.header_file = request.FILES['col_header_file']

			if request.POST['header_separator'] == 'Comma':
				get_record.header_separator = ','
			else:
				get_record.header_separator = '|'

		else:
			get_record.header = True


		get_record.uploaded_file_format = request.POST['file_type']
	
		


		# adding code field infos
		if 'code_field' in request.POST.keys() and request.POST['code_field'] == 'Yes':
			get_record.code_column_present = True

			get_record.code_column_text = request.POST['code_field_text']

			get_record.code_column_row_separator = request.POST['code_field_row_separator']

			get_record.code_column_field_separator = request.POST['code_field_col_separator']


		get_record.table_name = 'cr'+str(request.POST['result_id'])
		get_record.save()

		print "I am befor function"

		# if get_record.uploaded_file_format == 'txt':
		msg = process_text_file(request, get_record.id)

		
		return JsonResponse({'status':1, 'message':'Success'})

	
	else:
		return JsonResponse({"status":0, 'message':'Access Denied'})






@login_required
def process_text_file(request, record_id):
	print "I am here"

	if not rc_info.objects.filter(id=record_id).exists():
		return JsonResponse({'status':0, 'message':'Invalid Request Sent'})

	get_record = rc_info.objects.get(id=record_id)

	separator = get_record.separator
	db_columns = ''

	#=================== For single data file ==============================
	if get_record.main_file != None and get_record.main_file != '':

		with open("./media/"+str(get_record.main_file)) as file:
			data_line = file.readline()
			no_of_lines = file.readlines()

		# storing the line terminator
		if data_line[-2:] == '\r\n':
			get_record.main_line_terminator = data_line[-2:]

		else:
			get_record.main_line_terminator = data_line[-1:]


		# if header file is present
		if not get_record.header:
			header_separator = get_record.header_separator

			with open("./media/"+str(get_record.header_file)) as file:
				header_line = file.readline()

			if len(data_line.split(separator)) != len(header_line.split(header_separator)):
				return "Columns Mismatch Error"

			if header_separator == ',':
				get_record.original_columns = header_line.replace(',', '|')

			else:
				get_record.original_columns = header_line

			for i in range(len(header_line.split(header_separator))):
				db_columns = db_columns+'c'+str(i+1)+'|'

		# if header file is not present 
		else:
			if separator == ',':
				get_record.original_columns = data_line.replace(',', '|')

			elif separator == ':':
				get_record.original_columns = data_line.replace(':', '|')

			else:
				get_record.original_columns = data_line



			for i in range(len(data_line.split(separator))):
				db_columns = db_columns+'c'+str(i+1)+'|'


		get_record.no_of_columns = len(data_line.split(separator))
		get_record.database_columns = db_columns[:-1]

		get_record.no_of_rows = len(no_of_lines)

		get_record.save()


	#============================ For multiple data file ==========================
	else:
		cursor = connection.cursor()

		separator = ','

		count = 0

		found_head = False
		found_body = False
		found_foot = False

		if get_record.head_file != None and get_record.head_file != '':

			file_name = "./media/"+str(get_record.head_file)

			table_name = 'hd'+str(get_record.result_id)

			with open(file_name) as head_file:
				line = head_file.readline()

			# storing the line terminator
			if line[-2:] == '\r\n':
				get_record.head_line_terminator = line[-2:]

			else:
				get_record.head_line_terminator = line[-1:]

			get_record.save()

			
			fields = line.split(separator)

			query_fileds = ''

			for i in range(len(fields)):

				query_fileds = query_fileds+'c'+str(i+1)+' varchar(255),'

				count = count + 1

			query_fileds = query_fileds[:-1]

			table_query = "CREATE TABLE "+table_name+" ("+query_fileds+");"

			cursor.execute(table_query)


			raw_insert_query = "LOAD DATA LOCAL INFILE '"+file_name+"' INTO TABLE "+table_name+\
							" FIELDS TERMINATED BY '"+separator+"' LINES TERMINATED BY '"+str(get_record.head_line_terminator)+"';"

			print '-->',raw_insert_query

			cursor.execute(raw_insert_query)

			found_head = True


		if get_record.body_file != get_record.head_file and get_record.body_file != None and get_record.body_file != '':


			file_name = "./media/"+str(get_record.body_file)

			table_name = 'bd'+str(get_record.result_id)

			with open(file_name) as body_file:
				line = body_file.readline()

			# storing the line terminator
			if line[-2:] == '\r\n':
				get_record.body_line_terminator = line[-2:]

			else:
				get_record.body_line_terminator = line[-1:]

			get_record.save()


			fields = line.split(separator)

			# print 'fields :',fields


			query_fileds = ''
			
			for i in range(count, count+ len(fields)):

				query_fileds = query_fileds+'c'+str(i+1)+' varchar(255),'

				count = count +1

			query_fileds = query_fileds[:-1]

			table_query = "CREATE TABLE "+table_name+" ("+query_fileds+");"

			cursor.execute(table_query)


			raw_insert_query = "LOAD DATA LOCAL INFILE '"+file_name+"' INTO TABLE "+table_name+\
							" FIELDS TERMINATED BY '"+separator+"' LINES TERMINATED BY '"+str(get_record.body_line_terminator)+"';"

			print '-->',raw_insert_query


			cursor.execute(raw_insert_query)

			found_body = True



		if get_record.footer_file != get_record.body_file and get_record.footer_file != None and get_record.footer_file != '':

			print "I am in footer"


			file_name = "./media/"+str(get_record.footer_file)

			table_name = 'ft'+str(get_record.result_id)

			with open(file_name) as footer_file:
				line = footer_file.readline()

			# storing the line terminator
			if line[-2:] == '\r\n':
				get_record.foot_line_terminator = line[-2:]

			else:
				get_record.foot_line_terminator = line[-1:]

			get_record.save()


			fields = line.split(separator)

			# print 'fields :',fields

			query_fileds = ''

			for i in range(count, count+ len(fields)):

				query_fileds = query_fileds+'c'+str(i+1)+' varchar(255),'

			query_fileds = query_fileds[:-1]

			table_query = "CREATE TABLE "+table_name+" ("+query_fileds+");"

			cursor.execute(table_query)


			raw_insert_query = "LOAD DATA LOCAL INFILE '"+file_name+"' INTO TABLE "+table_name+\
							" FIELDS TERMINATED BY '"+separator+"' LINES TERMINATED BY '"+str(get_record.foot_line_terminator)+"';"


			print '-->',raw_insert_query


			cursor.execute(raw_insert_query)

			found_foot = True	


		original_columns = ''

		if found_head:
			file_name = "./media/"+str(get_record.head_file)
		
			with open(file_name) as head_file:
				line = head_file.readline()


			line = line.replace(str(get_record.head_line_terminator), '')
			line = line.split(separator)

			for l in line:
				original_columns = original_columns+l+'|'

			# original_columns = original_columns[:-1]




		if found_body:
			file_name = "./media/"+str(get_record.body_file)
			
			with open(file_name) as head_file:
				line = head_file.readline()

			line = line.replace(str(get_record.body_line_terminator), '')
			line = line.split(separator)

			for l in line:
				original_columns = original_columns+l+'|'

			# original_columns = original_columns[:-1]



		if found_foot:
			file_name = "./media/"+str(get_record.footer_file)
			
			with open(file_name) as head_file:
				line = head_file.readline()

			line = line.replace(str(get_record.foot_line_terminator), '')
			line = line.split(separator)

			for l in line:
				original_columns = original_columns+l+'|'



		original_columns = original_columns[:-1]

		get_record.original_columns = original_columns

		get_record.no_of_columns = len(original_columns.split('|'))


		db_columns = ''

		for i in range(len(original_columns.split('|'))):
			db_columns = db_columns+'c'+str(i+1)+'|'

		get_record.database_columns = db_columns[:-1]


		get_record.save()

		# msg = merge_tables(request, get_record.id)

	return 'Success'









#=============================== design part ================================

@login_required
def design_header(request, record_id):
	if not rc_info.objects.filter(id=record_id).exists():
		return HttpResponse("Invalid Request Sent")

	get_record = rc_info.objects.get(id=record_id)
	

	exam_id = get_record.result_id

	if get_record.no_of_files_uploaded == 1:

		fields = str(get_record.original_columns).split('|')

	else:
		file_name = "./media/"+str(get_record.head_file)

		with open(file_name) as file:
			line = file.readline()

		fields = line.split(get_record.separator)

	found_prompt = []
	

	if get_record.no_of_files_uploaded == 1:

		if get_record.innova_columns != None and get_record.innova_columns != '':
			found_prompt = str(get_record.innova_columns).split('|')

	else:
		if get_record.head_prompt != None and get_record.head_prompt != '':
			found_prompt = str(get_record.head_prompt).split('|')


	if cell_mapping.objects.filter(for_record=get_record,field_type='header').exists():
		header_table = create_dynamic_table(request, record_id, 'header')

	else: 
		header_table = ''

	finalized = get_record.finalized


	return render(request, 'header_page.html', {'head_row':range(10), 'record_id':record_id, 'finalized':finalized,
								'fields':fields,'found_prompt':found_prompt, 'header_table':header_table,
								'code_present':get_record.code_column_present, 'exam_id':exam_id })




@login_required
def design_body(request, record_id):
	if not rc_info.objects.filter(id=record_id).exists():
			return HttpResponse("Invalid Request Sent")

	get_record = rc_info.objects.get(id=record_id)
	# no_of_columns = get_record.no_of_columns

	# fields = str(get_record.original_columns).split('|')

	count = 0

	if get_record.no_of_files_uploaded == 1:

		fields = str(get_record.original_columns).split('|')

	else:
		file_name = "./media/"+str(get_record.body_file)

		with open(file_name) as file:
			line = file.readline()

		fields = line.split(get_record.separator)



		if get_record.head_file != get_record.body_file:
			# To get count of fields of previous file
			head_file_name = "./media/"+str(get_record.head_file)

			with open(head_file_name) as file:
				head_line = file.readline()

			count = len(head_line.split(get_record.separator))





	found_prompt = []
	

	if get_record.no_of_files_uploaded == 1:

		if get_record.innova_columns != None and get_record.innova_columns != '':
			found_prompt = str(get_record.innova_columns).split('|')

	else:
		if get_record.body_prompt != None and get_record.body_prompt != '':
			found_prompt = str(get_record.body_prompt).split('|')

		
	# 	search_fields = str(get_record.search_columns).split('|')

	# if get_record.code_columns:
	# 	code_fields = str(get_record.code_columns).split('|')


	if cell_mapping.objects.filter(for_record=get_record,field_type='body').exists():
		body_header, body_table = create_dynamic_table(request, record_id, 'body')

	else: 
		body_table = ''
		body_header = ''
	
	finalized = get_record.finalized

	return render(request, 'body_page.html', {'body_row':range(45), 'record_id':record_id, 'count':count,
							'fields':fields,'found_prompt':found_prompt, 'body_table':body_table, 'body_header':body_header,
							'code_present':get_record.code_column_present, 'finalized':finalized})





@login_required
def design_footer(request, record_id):
	if not rc_info.objects.filter(id=record_id).exists():
			return HttpResponse("Invalid Request Sent")

	get_record = rc_info.objects.get(id=record_id)
	# no_of_columns = get_record.no_of_columns

	count = 0

	if get_record.no_of_files_uploaded == 1:

		fields = str(get_record.original_columns).split('|')

	else:
		file_name = "./media/"+str(get_record.footer_file)

		with open(file_name) as file:
			line = file.readline()

		fields = line.split(get_record.separator)

		if get_record.footer_file != get_record.body_file:

			# To get count of fields of previous file
			body_file_name = "./media/"+str(get_record.body_file)

			with open(body_file_name) as file:
				body_line = file.readline()

			head_file_name = "./media/"+str(get_record.head_file)

			with open(head_file_name) as file:
				head_line = file.readline()			

			count = len(body_line.split(get_record.separator))+len(head_line.split(get_record.separator))

		else:
			print "I am in else part"
			head_file_name = "./media/"+str(get_record.head_file)

			with open(head_file_name) as file:
				head_line = file.readline()

			count = len(head_line.split(get_record.separator))
			print count
	

	found_prompt = []

	if get_record.no_of_files_uploaded == 1:

		if get_record.innova_columns != None and get_record.innova_columns != '':
			found_prompt = str(get_record.innova_columns).split('|')

	else:
		if get_record.footer_prompt != None and get_record.footer_prompt != '':
			found_prompt = str(get_record.footer_prompt).split('|')
	

	# if get_record.innova_columns:
	# 	found_prompt = str(get_record.innova_columns).split('|')

		
	# 	search_fields = str(get_record.search_columns).split('|')

	# if get_record.code_columns:
	# 	code_fields = str(get_record.code_columns).split('|')

	if cell_mapping.objects.filter(for_record=get_record,field_type='footer').exists():
		footer_table = create_dynamic_table(request, record_id, 'footer')

	else: 
		footer_table = ''
	
	
	finalized = get_record.finalized

	return render(request, 'footer_page.html', {'head_row':range(10), 'record_id':record_id, 'count':count,
							'fields':fields,'found_prompt':found_prompt, 'footer_table':footer_table,
							 'code_present':get_record.code_column_present, 'finalized':finalized})





@login_required
def add_design(request, record_id):
	if request.method == 'POST':
		

		if not rc_info.objects.filter(id=record_id).exists():
			return JsonResponse({'status':0, 'message':'Wrong ID Provided'})

		get_record = rc_info.objects.get(id=record_id)

		auto_fields = []
		
		if get_record.auto_prompt != None:
			auto_fields = str(get_record.auto_prompt).split('|')


		if cell_mapping.objects.filter(field_type=request.POST['section']).exists():
			cell_mapping.objects.filter(field_type=request.POST['section']).delete()

		if 'section' in request.POST.keys() and request.POST['section'] == 'header':
			get_record.header_columns = ''
		
		
		elif 'section' in request.POST.keys() and request.POST['section'] == 'body':
			get_record.body_columns = ''
		

		elif 'section' in request.POST.keys() and request.POST['section'] == 'footer':

			if get_record.search_columns == None or get_record.search_columns == '':
				return JsonResponse({'status':0, 'message':'You must select at least one search field'})

			get_record.footer_columns = ''

		get_record.save()

		# ================== Validation Checking ====================

		# items = []
		# for key in request.POST.keys():
		# 	print request.POST[key]
			
		# 	if key != 'csrfmiddlewaretoken':
		# 		if not request.POST[key] in items:
		# 			items.append(request.POST[key])
		# 			print request.POST[key]

		# 		else:
		# 			del items[:]
		# 			return JsonResponse({'status':0, 'message':'You can not put same value twice'});
				

		#=============== column name mapping ====================

		# column_map = {}

		# db_columns = str(get_record.database_columns).split('|')
		# innova_columns = str(get_record.innova_columns).split('|')

		# for i in range(len(db_columns)):
		# 	column_map[db_columns[i]] = innova_columns[i]

		#=========================================================

		design_dict = {}

		for key in request.POST.keys():

			if key != 'csrfmiddlewaretoken' and request.POST[key] != '':

				if request.POST[key].find('|') > -1:


					temp_val = request.POST[key].split('|')

					# column name c1, c2 etc
					column_value = temp_val[1]

					# Edited Column Name
					# column_text = column_map[column_value] 
					column_text = temp_val[0]


					#==================== getting previous cell name (auto prompt) ===============
					if column_value in auto_fields:
					
						temp_key_string = unicodedata.normalize('NFKD', key).encode('ascii','ignore')

						temp_key_string = list(temp_key_string)
					
						temp_key_string[2] = chr(ord(key[2]) - 1) 

						temp_key_string = "".join(temp_key_string)

						design_dict[temp_key_string] = column_text

						#==========================================================================
					
					design_dict[key] = column_text+'|'+column_value

					#==============================================================================


				else:
					# ========== To store normal text ========
					design_dict[key] = request.POST[key]


		for key in design_dict.keys():

			if key[:2] == 'HR' and str(key[3]).isdigit():

				create_record = cell_mapping.objects.create(for_record=get_record, key=key, value=design_dict[key], field_type='header')

				# storing header columns
				if str(design_dict[key]).find('|') > -1:

					temp_string = str(design_dict[key]).split('|')

					if get_record.header_columns == '':
						get_record.header_columns = str(temp_string[1])

					else:
						get_record.header_columns = str(get_record.header_columns)+'|'+str(temp_string[1])



			elif key[:2] == 'BH' and str(key[2]).isdigit():

				create_record = cell_mapping.objects.create(for_record=get_record, key=key, value=design_dict[key], field_type='body')



			elif key[:2] == 'BS' and str(key[3]).isdigit():

				create_record = cell_mapping.objects.create(for_record=get_record, key=key, value=design_dict[key], field_type='body')

				# storing body columns
				if str(design_dict[key]).find('|') > -1:

					temp_string = str(design_dict[key]).split('|')

					if get_record.body_columns == '':
						get_record.body_columns = str(temp_string[1])
					
					else:
						get_record.body_columns = str(get_record.body_columns)+'|'+str(temp_string[1])


			elif key[:2] == 'FR' and str(key[3]).isdigit():

				create_record = cell_mapping.objects.create(for_record=get_record, key=key, value=design_dict[key], field_type='footer')

				# storing header columns
				if str(design_dict[key]).find('|') > -1:

					temp_string = str(design_dict[key]).split('|')

					if get_record.footer_columns == '':
						get_record.footer_columns = str(temp_string[1])

					else:
						get_record.footer_columns = str(get_record.footer_columns)+'|'+str(temp_string[1])


		get_record.save()

		return JsonResponse({'status':1})

	return JsonResponse({'status':0, 'message':'Access Denied'})





@login_required
def create_dynamic_table(request, record_id, keyword):
	if not rc_info.objects.filter(id=record_id).exists():
		return JsonResponse({'status':0, 'message':'Wrong ID Provided'})

	get_record = rc_info.objects.get(id=record_id)

	
	design_dict = {}

	temp_record = cell_mapping.objects.filter(for_record=get_record,field_type=keyword)

	for t in temp_record:
		design_dict[t.key] = t.value


	if keyword == 'header':
		head_table_td = ''

		for i in range(10):
			head_table_td = head_table_td+'<tr style=" background:rgba(255,255,255,0.4);">\n'
		
			for alpha in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'):

				if 'HR'+alpha+str(i+1) in design_dict.keys():
				

					temp_val = design_dict['HR'+alpha+str(i+1)]
						# head_table_td = head_table_td+'<td> <label> '+design_dict['HR'+alpha+str(i+1)]+'</label> </td>'
					head_table_td = head_table_td+'<td> <input type="text" name="HR'+alpha+str(i+1)+'" value="'+temp_val+'" class="form-control inputtype1 dropdiv"> </td>\n'

				else:
					# head_table_td = head_table_td+ '<td><label>&nbsp;</label></td>'
					head_table_td = head_table_td+ '<td><input type="text" name="HR'+alpha+str(i+1)+'" value=""	class="form-control inputtype1 dropdiv"></td>\n'


			head_table_td = head_table_td+'</tr>\n'

	

		return head_table_td


	if keyword == 'body':
	
		body_table_td = ''

		body_header_td = ''	
	
		# for body header
		#-----------------
		body_header_td = body_header_td+'<tr style=" background:rgba(255,255,255,0.4);">\n'
		for i in range(10):			

			if 'BH'+str(i+1) in design_dict.keys():

				temp_val = design_dict['BH'+str(i+1)]
				
				# body_header_td = body_header_td + '<td> <label>'+design_dict['BH'+str(i+1)]+'</label> </td>'
				body_header_td = body_header_td + '<td><input type="text" name="BH'+str(i+1)+'" value="'+temp_val+'" class="form-control inputtype1 dropdiv"> </td>\n'

			else:
				body_header_td = body_header_td + '<td> <input type="text" name="BH'+str(i+1)+'" value="" class="form-control inputtype1 dropdiv"> </td>\n'

		body_header_td = body_header_td+'</tr>\n'

	
		# for body section table
		#-------------------------
		for i in range(45):
			body_table_td = body_table_td+'<tr style=" background:rgba(255,255,255,0.4);">'

			for alpha in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'):

				if 'BS'+alpha+str(i+1) in design_dict.keys():
					
					temp_val = design_dict['BS'+alpha+str(i+1)]

				
					# body_table_td = body_table_td+'<td> <label> '+design_dict['BS'+alpha+str(i+1)]+'</label> </td>'
					body_table_td = body_table_td+'<td> <input type="text" name="BS'+alpha+str(i+1)+'" value="'+temp_val+'" class="form-control inputtype1 dropdiv"> </td>\n'

				else:
					body_table_td = body_table_td+'<td> <input type="text" name="BS'+alpha+str(i+1)+'" value="" class="form-control inputtype1 dropdiv"> </td>\n'


			body_table_td = body_table_td+'</tr>\n'

		return body_header_td, body_table_td

	if keyword == 'footer':

		foot_table_td = ''
	
		# for footer section table
		#-------------------------
		for i in range(10):
			foot_table_td = foot_table_td+'<tr style=" background:rgba(255,255,255,0.4);">\n'

			for alpha in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'):

				if 'FR'+alpha+str(i+1) in design_dict.keys():
					

					temp_val = design_dict['FR'+alpha+str(i+1)]

					
					# foot_table_td = foot_table_td+'<td> <label> '+design_dict['FR'+alpha+str(i+1)]+'</label> </td>'
					foot_table_td = foot_table_td+'<td> <input type="text" name="FR'+alpha+str(i+1)+'" value="'+temp_val+'" class="form-control inputtype1 dropdiv"> </td>\n'

				else:
					# foot_table_td = foot_table_td+'<td> <label>&nbsp; </label> </td>'
					foot_table_td = foot_table_td+'<td> <input type="text" name="FR'+alpha+str(i+1)+'" value="" class="form-control inputtype1 dropdiv"> </td>\n'


			foot_table_td = foot_table_td+'</tr>\n'

		return foot_table_td






@login_required
def create_multi_value_table(request, record_id, design_dict):

	if not rc_info.objects.filter(id=record_id).exists():
		return JsonResponse({'status':0, 'message':'Wrong ID Provided'})

	get_record = rc_info.objects.get(id=record_id)

	cursor = connection.cursor()

	table_name = get_record.table_name

	# # to get the current Database name
	# db_name = connection.settings_dict['NAME']

	# query =  "SELECT column_name FROM information_schema.columns WHERE table_name = '"+table_name+"' AND table_schema = '"+db_name+"';"

	# cursor.execute(query)

	# col_result = cursor.fetchall()

	# all_columns = []

	# for c in col_result:
	# 	all_columns.append(c[0])

	code_columns = str(get_record.code_columns).split('|')


	# print 'design_dict -->', design_dict.values()

	print 'code columns -->', code_columns


	# creating the tables dynamically
	#================================== 
	head_table_td = ''
	body_table_td = ''
	foot_table_td = ''

	body_header_td = ''

	has_row = False

	temp_string = []
	#-------------------------
	for i in range(10):
		head_table_td = head_table_td+'<tr>'
	
		for alpha in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'):

			if 'HR'+alpha+str(i+1) in design_dict.keys():
				has_row = True

				temp_val = design_dict['HR'+alpha+str(i+1)]

				print 'temp val -->', temp_val

				if temp_val.find('|') > -1:
					temp = temp_val.split('|')

					if temp[1] in code_columns:
						print 'found'

						head_table_td = head_table_td+'<td> <label> '+temp[0]+ ' (code)'+'</label> </td>'
					else:

						temp = temp[0]

						head_table_td = head_table_td+'<td> <label> '+temp+ ' value'+'</label> </td>'
				else:
				
					head_table_td = head_table_td+'<td> <label> '+design_dict['HR'+alpha+str(i+1)]+'</label> </td>'

			else:
				head_table_td = head_table_td+ '<td><label>&nbsp;</label></td>'


		head_table_td = head_table_td+'</tr>\n'


		
	
	#=================== removing blank rows========================

		if has_row:
			has_row = False

			temp_string.append(head_table_td)
		
		
		head_table_td = ''
			

	head_table_td = ''

	for t in temp_string:
		
		head_table_td = head_table_td+t+'\n'

	del temp_string[:]

	#==============================================================#
			

	has_row = False
	body_header_td = body_header_td+'<tr>'
	for i in range(10):
		

		if 'BH'+str(i+1) in design_dict.keys():
			has_row = True

			temp_val = design_dict['BH'+str(i+1)]

			if temp_val.find('|') > -1:
				temp = temp_val.split('|')
				temp = temp[0]
				body_header_td = body_header_td + '<td> <label>'+temp+ ' value'+'</label> </td>'
			
			else:
			
				body_header_td = body_header_td + '<td> <label>'+design_dict['BH'+str(i+1)]+'</label> </td>'

		else:
			body_header_td = body_header_td + '<td> <label> &nbsp;</label> </td>'

	body_header_td = body_header_td+'</tr>'

	if not has_row:
		body_header_td=''


	print body_header_td

	

	has_row = False
	# for body section table
	#-------------------------
	for i in range(45):
		body_table_td = body_table_td+'<tr>'

		for alpha in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'):

			if 'BS'+alpha+str(i+1) in design_dict.keys():
				has_row = True

				temp_val = design_dict['BS'+alpha+str(i+1)]
			

				if temp_val.find('|') > -1:
					temp = temp_val.split('|')
					if temp[1] in code_columns:
						body_table_td = body_table_td+'<td> <label> '+temp[0]+ ' code'+'</label> </td>'

					else:
						temp = temp[0]
						body_table_td = body_table_td+'<td> <label> '+temp+ ' value'+'</label> </td>'

				else:
					
					body_table_td = body_table_td+'<td> <label> '+temp_val+'</label> </td>'

			else:
				body_table_td = body_table_td+'<td> <label> &nbsp; </label> </td>'


		body_table_td = body_table_td+'</tr>\n'

	# # ================== blank row removing ==============

		if has_row:
			has_row = False

			temp_string.append(body_table_td)

		

		body_table_td = ''


	for t in temp_string:

		body_table_td = body_table_td+t+'\n'

	del temp_string[:]
	# #========================================================


	has_row = False
	# for footer section table
	#-------------------------
	for i in range(10):
		foot_table_td = foot_table_td+'<tr>'

		for alpha in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'):

			if 'FR'+alpha+str(i+1) in design_dict.keys():
				has_row = True

				temp_val = design_dict['FR'+alpha+str(i+1)]

				if temp_val.find('|') > -1:
					temp = temp_val.split('|')
					if temp[1] in code_columns:
						foot_table_td = foot_table_td+'<td> <label> '+temp[0]+ ' code'+'</label> </td>'

					else:
						temp = temp[0]

						foot_table_td = foot_table_td+'<td> <label> '+temp+ ' value'+'</label> </td>'
				else:
				
					foot_table_td = foot_table_td+'<td> <label> '+design_dict['FR'+alpha+str(i+1)]+'</label> </td>'

			else:
				foot_table_td = foot_table_td+'<td> <label>&nbsp; </label> </td>'


		foot_table_td = foot_table_td+'</tr>\n'

		# # ================== blank row removing ==============

		if has_row:
			has_row = False

			temp_string.append(foot_table_td)


		foot_table_td = ''


	for t in temp_string:
		
		foot_table_td = foot_table_td+t+'\n'

	del temp_string[:]
	# #========================================================

	return (head_table_td, body_header_td, body_table_td, foot_table_td)





@login_required
def create_preview_table(request, record_id, design_dict):

	if not rc_info.objects.filter(id=record_id).exists():
		return JsonResponse({'status':0, 'message':'Wrong ID Provided'})

	get_record = rc_info.objects.get(id=record_id)

	# design_dict = request.session['design_dict']

	code_columns = str(get_record.code_columns).split('|')


	# creating the tables dynamically
	#================================== 
	head_table_td = ''
	body_table_td = ''
	foot_table_td = ''

	body_header_td = ''

	has_row = False

	temp_string = []
	#-------------------------
	for i in range(10):
		head_table_td = head_table_td+'<tr>'
	
		for alpha in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'):

			if 'HR'+alpha+str(i+1) in design_dict.keys():
				has_row = True

				temp_val = design_dict['HR'+alpha+str(i+1)]

				if temp_val.find('|') > -1:
					temp = temp_val.split('|')

					if temp[1] in code_columns:

						head_table_td = head_table_td+'<td> <label> '+temp[0]+ ' (code)'+'</label> </td>'
					else:

						temp = temp[0]

						head_table_td = head_table_td+'<td> <label> '+temp+ ' value'+'</label> </td>'
				else:
				
					head_table_td = head_table_td+'<td> <label> '+design_dict['HR'+alpha+str(i+1)]+'</label> </td>'

			else:
				head_table_td = head_table_td+ '<td><label>&nbsp;</label></td>'


		head_table_td = head_table_td+'</tr>\n'


		
	
	#=================== removing blank rows========================

		if has_row:
			has_row = False

			temp_string.append(head_table_td)
		
		
		head_table_td = ''
			

	head_table_td = ''

	for t in temp_string:
		
		head_table_td = head_table_td+t+'\n'

	del temp_string[:]

	#==============================================================#
			

	has_row = False
	body_header_td = body_header_td+'<tr>'
	for i in range(10):
		

		if 'BH'+str(i+1) in design_dict.keys():
			has_row = True

			temp_val = design_dict['BH'+str(i+1)]

			if temp_val.find('|') > -1:
				temp = temp_val.split('|')
				temp = temp[0]
				body_header_td = body_header_td + '<td> <label>'+temp+ ' value'+'</label> </td>'
			
			else:
			
				body_header_td = body_header_td + '<td> <label>'+design_dict['BH'+str(i+1)]+'</label> </td>'

		else:
			body_header_td = body_header_td + '<td> <label> &nbsp;</label> </td>'

	body_header_td = body_header_td+'</tr>'

	if not has_row:
		body_header_td=''


	print body_header_td

	

	has_row = False
	# for body section table
	#-------------------------
	for i in range(45):
		body_table_td = body_table_td+'<tr>'

		for alpha in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'):

			if 'BS'+alpha+str(i+1) in design_dict.keys():
				has_row = True

				temp_val = design_dict['BS'+alpha+str(i+1)]

			

				if temp_val.find('|') > -1:
					temp = temp_val.split('|')
					if temp[1] in code_columns:
						body_table_td = body_table_td+'<td> <label> '+temp[0]+ ' code'+'</label> </td>'

					else:
						temp = temp[0]
						body_table_td = body_table_td+'<td> <label> '+temp+ ' value'+'</label> </td>'

				else:
					body_table_td = body_table_td+'<td> <label> '+design_dict['BS'+alpha+str(i+1)]+'</label> </td>'

			else:
				body_table_td = body_table_td+'<td> <label> &nbsp; </label> </td>'


		body_table_td = body_table_td+'</tr>\n'

	# # ================== blank row removing ==============

		if has_row:
			has_row = False

			temp_string.append(body_table_td)

		

		body_table_td = ''


	for t in temp_string:

		body_table_td = body_table_td+t+'\n'

	del temp_string[:]
	# #========================================================


	has_row = False
	# for footer section table
	#-------------------------
	for i in range(45):
		foot_table_td = foot_table_td+'<tr>'

		for alpha in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'):

			if 'FR'+alpha+str(i+1) in design_dict.keys():
				has_row = True

				temp_val = design_dict['FR'+alpha+str(i+1)]

				if temp_val.find('|') > -1:
					temp = temp_val.split('|')
					if temp[1] in code_columns:
						foot_table_td = foot_table_td+'<td> <label> '+temp[0]+ ' code'+'</label> </td>'

					else:
						temp = temp[0]

						foot_table_td = foot_table_td+'<td> <label> '+temp+ ' value'+'</label> </td>'
				else:
				
					foot_table_td = foot_table_td+'<td> <label> '+design_dict['FR'+alpha+str(i+1)]+'</label> </td>'

			else:
				foot_table_td = foot_table_td+'<td> <label>&nbsp; </label> </td>'


		foot_table_td = foot_table_td+'</tr>\n'

		# # ================== blank row removing ==============

		if has_row:
			has_row = False

			temp_string.append(foot_table_td)


		foot_table_td = ''


	for t in temp_string:
		
		foot_table_td = foot_table_td+t+'\n'

	del temp_string[:]
	# #========================================================

	return (head_table_td, body_header_td, body_table_td, foot_table_td)


#=============================== design part ends =============================





@login_required
def preview(request, record_id):
	if not rc_info.objects.filter(id=record_id).exists():
		return JsonResponse({'status':0, 'message':'Wrong ID Provided'})


	get_record = rc_info.objects.get(id=record_id)

	finalized = get_record.finalized


	if get_record.no_of_files_uploaded == 1:

		the_file = "./media/"+str(get_record.main_file)

		with open(the_file) as file:
			lines = file.readlines()

		no_of_records = len(lines)

	else:

		no_of_records = 'Not Available'

	design_dict = {}



	if cell_mapping.objects.filter(for_record=get_record).exists():

		found = True

		temp_record = cell_mapping.objects.filter(for_record=get_record)

		for t in temp_record:
			design_dict[t.key] = t.value

		

		head_table_td, body_header_td, body_table_td, foot_table_td = create_preview_table(request, record_id, design_dict)

		

		return render(request, 'preview.html', {'header_table':head_table_td, 'body_header':body_header_td, 
												'no_of_records':no_of_records, 'finalized':finalized,
												'body_table':body_table_td, 'footer_table':foot_table_td, 'record_id':record_id})
	else:
		found = False
		


		return render(request, 'preview.html', {'found':found, 'no_of_records':no_of_records, 'record_id':record_id, 
													'finalized':finalized})






@login_required
def finalize(request, record_id):

	if not rc_info.objects.filter(id=record_id).exists():
		return JsonResponse({'status':0, 'message':'Wrong ID Provided'})

	if request.method == 'POST':

		get_record = rc_info.objects.get(id=record_id)


		if get_record.no_of_files_uploaded == 1:

			result = make_raw_query(request, record_id)

		elif get_record.no_of_files_uploaded > 1:

			result = merge_tables(request, record_id) 

		# get_record.finalized = True

		# get_record.save()

		return JsonResponse({'status':1})

	else:

		
		return JsonResponse({'status':0, 'message':'Access Denied'})





#===================================== Database Operations =======================================#



@login_required
def add_records(request, record_id):
	if request.method == 'POST':

		if not rc_info.objects.filter(id=record_id).exists():
			return JsonResponse({'status':0, 'message':'Wrong ID Provided'})

		get_record = rc_info.objects.get(id=record_id)

		#========================= for search fields =======================
		if 'search' in request.POST.keys():

			if get_record.search_columns != None and get_record.search_columns != '':
				get_search_count = len(str(get_record.search_columns).split('|'))

				if len(request.POST.getlist('search')) + get_search_count > 3:
					return JsonResponse({'status':0, 'message':'You can not use more than 3 search fields in total'})

				else:
					temp_text = ''
					for g in request.POST.getlist('search'):
						temp_text = temp_text+'c'+str(g)+'|'

					get_record.search_columns = str(get_record.search_columns)+'|'+temp_text[:-1]

					get_record.save()

			else:

				if request.POST['section'] == 'footer':
					return JsonResponse({'status':0, 'message':'You have not choose any search field at all. Please choose at least 1 search field'})

				temp_text = ''
				for g in request.POST.getlist('search'):
					temp_text = temp_text+'c'+str(g)+'|'

				get_record.search_columns = temp_text[:-1]

				get_record.save()

		#======================================================================#

		if request.POST['section'] == 'header': 
			if get_record.no_of_files_uploaded == 1:
				file_name = "./media/"+str(get_record.main_file)

			else:
				file_name = "./media/"+str(get_record.head_file)

			with open(file_name) as file:
				line = file.readline()

			line = line.split(str(get_record.separator))

			no_of_columns = len(line)

			#=================== Validation Checking ========================

			blank_field = False
			has_search = False
			search_count = 0


			for i in range(no_of_columns):

				if request.POST['get_prompt'+str(i+1)] == '':
					blank_field = True

				# if len(request.POST.getlist('search'+str(i+1))) > 0:
				# 	has_search = True
				# 	search_count = search_count + 1

			# if search_count > 3:
			# 	return JsonResponse({'status':0, 'message':'You can not select search fields more than three'})

			if blank_field:
				return JsonResponse({'status':0, 'message':'You can leave blank fields'})

			#===================== Validation Ends =========================
			


			#====================== Adding Records =========================

			edited_fields = ''
			search_fields = ''
			code_fields = ''
			auto_fields = ''

			for i in range(no_of_columns):

				edited_fields = edited_fields+request.POST['get_prompt'+str(i+1)]+'|'

				# if len(request.POST.getlist('search'+str(i+1))) > 0:
				# 	search_fields = search_fields+'c'+str(i+1)+'|'

				if len(request.POST.getlist('code'+str(i+1))) > 0:
					code_fields = code_fields+'c'+str(i+1)+'|'

				if request.POST["auto_prompt"+str(i+1)] == 'Yes':
					auto_fields = auto_fields+'c'+str(i+1)+'|'

					


			if get_record.no_of_files_uploaded == 1:
				get_record.innova_columns = edited_fields[:-1]

			if edited_fields != '':
				get_record.head_prompt = edited_fields[:-1]

			# if search_fields != '':
			# 	get_record.search_columns = search_fields[:-1]

			if code_fields != '':
				get_record.code_columns = code_fields[:-1]

			if auto_fields != '':
				get_record.auto_prompt = auto_fields[:-1]



			

			#====================== Adding Records Ends ====================



		elif request.POST['section'] == 'body':
			if get_record.no_of_files_uploaded == 1:
				file_name = "./media/"+str(get_record.main_file)

			else:
				file_name = "./media/"+str(get_record.body_file)

			with open(file_name) as file:
				line = file.readline()

			line = line.split(get_record.separator)

			no_of_columns = len(line)

			#=================== Validation Checking ========================

			blank_field = False
			has_search = False
			search_count = 0

			for i in range(no_of_columns):

				if request.POST['get_prompt'+str(i+1)] == '':
					blank_field = True

				# if len(request.POST.getlist('search'+str(i+1))) > 0:
				# 	has_search = True
				# 	search_count = search_count + 1

			# if search_count > 3:
			# 	return JsonResponse({'status':0, 'message':'You can not select search fields more than three'})

			if blank_field:
				return JsonResponse({'status':0, 'message':'You can leave blank fields'})

			#===================== Validation Ends =========================

			#====================== Adding Records =========================

			edited_fields = ''
			search_fields = ''
			code_fields = ''
			auto_fields = ''

			for i in range(no_of_columns):

				edited_fields = edited_fields+request.POST['get_prompt'+str(i+1)]+'|'

				# if len(request.POST.getlist('search'+str(i+1))) > 0:
				# 	search_fields = search_fields+'c'+str(i+1)+'|'

				if len(request.POST.getlist('code'+str(i+1))) > 0:
					code_fields = code_fields+'c'+str(i+1)+'|'

				if request.POST["auto_prompt"+str(i+1)] == 'Yes':
					auto_fields = auto_fields+'c'+str(i+1)+'|'



			# if len(request.POST.getlist('search')) > 0:
			# 	search_fields = search_fields+'c'+str(i+1)+'|'

			if edited_fields != '':
				get_record.body_prompt = edited_fields[:-1]

			# if search_fields != '':
			# 	get_record.search_columns = search_fields[:-1]

			if code_fields != '':
				get_record.code_columns = code_fields[:-1]

			if auto_fields != '':
				get_record.auto_prompt = auto_fields[:-1]

			if get_record.no_of_files_uploaded == 1:
				get_record.innova_columns = edited_fields[:-1]

		

			#====================== Adding Records Ends ====================


		elif request.POST['section'] == 'footer':
			if get_record.no_of_files_uploaded == 1:
				file_name = "./media/"+str(get_record.main_file)

			else:
				file_name = "./media/"+str(get_record.footer_file)

			with open(file_name) as file:
				line = file.readline()

			line = line.split(get_record.separator)

			no_of_columns = len(line)


			#=================== Validation Checking ========================

			blank_field = False

			has_search = False

			search_count = 0

			for i in range(no_of_columns):

				if request.POST['get_prompt'+str(i+1)] == '':
					blank_field = True

			# 	if len(request.POST.getlist('search'+str(i+1))) > 0:
			# 		has_search = True
			# 		search_count = search_count + 1

			# if search_count > 3:
			# 	return JsonResponse({'status':0, 'message':'You can not select search fields more than three'})


			if blank_field:
				return JsonResponse({'status':0, 'message':'You can leave blank fields'})

			#===================== Validation Ends =========================


			#====================== Adding Records =========================

			edited_fields = ''
			search_fields = ''
			code_fields = ''
			auto_fields = ''

			for i in range(no_of_columns):

				edited_fields = edited_fields+request.POST['get_prompt'+str(i+1)]+'|'

				# if len(request.POST.getlist('search'+str(i+1))) > 0:
				# 	search_fields = search_fields+'c'+str(i+1)+'|'

				if len(request.POST.getlist('code'+str(i+1))) > 0:
					code_fields = code_fields+'c'+str(i+1)+'|'

				if request.POST["auto_prompt"+str(i+1)] == 'Yes':
					auto_fields = auto_fields+'c'+str(i+1)+'|'

			if edited_fields != '':
				get_record.footer_prompt = edited_fields[:-1]

			# if search_fields != '':
			# 	get_record.search_columns = search_fields[:-1]

			if code_fields != '':
				get_record.code_columns = code_fields[:-1]

			if auto_fields != '':
				get_record.auto_prompt = auto_fields[:-1]


			if get_record.no_of_files_uploaded == 1:
				get_record.innova_columns = edited_fields[:-1]

			

			#====================== Adding Records Ends ====================

		get_record.save()


		return JsonResponse({'status':1})


	return JsonResponse({'status':0, 'message':'Access Denied'})

	





@login_required
def reset_table(request, record_id):
	if request.method == 'POST':
		get_record = rc_info.objects.get(id=record_id)
		# ====================================
		
		print request.POST.keys()


		if get_record.no_of_files_uploaded == 1:
			get_record.innova_columns = ''

			get_record.search_columns = ''

			get_record.code_columns = ''

			get_record.auto_prompt = ''

			get_record.search_columns = ''

			get_record.save()

			return JsonResponse({'status':1})

		else:
			if request.POST['section'] == 'header':
				get_record.head_prompt = ''

			elif request.POST['section'] == 'body':
				get_record.body_prompt = ''

			elif request.POST['section'] == 'footer':
				get_record.footer_prompt = ''

			get_record.search_columns = ''

			get_record.save()

		#=================== Validation Checking ========================

		# blank_field = False

		# has_search = False

		# search_count = 0

		# for i in range(no_of_columns):

		# 	if request.POST['get_prompt'+str(i+1)] == '':
		# 		blank_field = True

		# 	if len(request.POST.getlist('search'+str(i+1))) > 0:
		# 		has_search = True
		# 		search_count = search_count + 1

		# if not has_search:
		# 	return JsonResponse({'status':0, 'message':'You must select at least one search field'})

		# if search_count > 3:
		# 	return JsonResponse({'status':0, 'message':'You can not select search fields more than three'})


		# if blank_field:
		# 	return JsonResponse({'status':0, 'message':'You can leave blank fields'})

		#===================== Validation Ends =========================


		#====================== Adding Records =========================

		# edited_fields = ''
		# search_fields = ''
		# code_fields = ''
		# auto_fields = ''

		# for i in range(no_of_columns):

		# 	edited_fields = edited_fields+request.POST['get_prompt'+str(i+1)]+'|'

		# 	if len(request.POST.getlist('search'+str(i+1))) > 0:
		# 		search_fields = search_fields+'c'+str(i+1)+'|'

		# 	if len(request.POST.getlist('code'+str(i+1))) > 0:
		# 		code_fields = code_fields+'c'+str(i+1)+'|'

		# 	if request.POST["auto_prompt"+str(i+1)] == 'Yes':
		# 		auto_fields = auto_fields+'c'+str(i+1)+'|'

		# if edited_fields != '':
		# 	get_record.innova_columns = edited_fields[:-1]

		# if search_fields != '':
		# 	get_record.search_columns = search_fields[:-1]

		# if code_fields != '':
		# 	get_record.code_columns = code_fields[:-1]

		# if auto_fields != '':
		# 	get_record.auto_prompt = auto_fields[:-1]

		# get_record.save()

		#====================== Adding Records Ends ====================


		return JsonResponse({'status':1})

	return JsonResponse({'status':0, 'message':'Access Denied'})



@login_required
def merge_tables(request, record_id):

	get_record = rc_info.objects.get(id=record_id)

	cursor = connection.cursor()

	# used for detecting index values
	i_count = 0

	separator = ','

	found_head = False
	found_body = False
	found_foot = False

	raw_query = ''


	if get_record.head_file != None and get_record.head_file != '':

		found_head = True

		header_file = "./media/"+str(get_record.head_file)
		
		with open(header_file) as file:

			line = file.readline()

		head_temp = line.split(separator)


		for h in head_temp:
			i_count = i_count + 1

			if get_record.head_primary_field == h:
				head_index = 'c'+str(i_count)



		head_table = 'hd'+str(get_record.result_id)


	if get_record.body_file != None and get_record.body_file != '' and get_record.body_file != get_record.head_file:
		found_body = True

		body_file = "./media/"+str(get_record.body_file)
		
		with open(body_file) as file:
			line = file.readline()

		body_temp = line.split(separator)

		for b in body_temp:
			i_count = i_count +1

			if get_record.body_primary_field == b:
				body_index = 'c'+str(i_count)


		body_table = 'bd'+str(get_record.result_id)





	if get_record.footer_file != None and get_record.footer_file != '' and get_record.footer_file != \
											get_record.head_file and get_record.footer_file != get_record.body_file:
		found_foot = True

		footer_file = "./media/"+str(get_record.footer_file)
		
		with open(footer_file) as file:
			line = file.readline()

		foot_temp = line.split(separator)

		for f in foot_temp:
			i_count = i_count +1

			if get_record.footer_primary_field == f:
				footer_index = 'c'+str(i_count)


		footer_table = 'ft'+str(get_record.result_id)
 	

	table_name = 'cr'+str(get_record.result_id)

	all_columns = ''
	count = 0

	# ========================= removing table if already exists ========================#

	check_query = "SHOW TABLES LIKE '"+table_name+"';"

	try:
		cursor.execute(check_query)

		check_table = cursor.fetchone();

		if len(check_table) > 0:
			delete_query = "DROP TABLE "+table_name+";"

			cursor.execute(delete_query)
	except:
		pass

	#=====================================================================================#

	#------------------------------ Getting Search Fields --------------------------------#

	index_fields = ''

	if get_record.search_columns != None and get_record.search_columns != '':

		if str(get_record.search_columns).find('|') > -1:

			index_fields = str(get_record.search_columns).replace('|', ',')

		else:
			index_fields = str(get_record.search_columns)


	#============================== making the query ====================================

	# ----------------- For Head, Body and Footer File ------------------
	if found_head and found_body and found_foot:
		print "1st case"

		for i in range(len(head_temp)):

			all_columns = all_columns+'t1.'+'c'+str(i+1)+', '
			count = count +1

		for i in range(count, count+ len(body_temp)):
			all_columns = all_columns+'t2.'+'c'+str(i+1)+', '
			count = count +1

		for i in range(count, count+ len(foot_temp)):
			all_columns = all_columns+'t3.'+'c'+str(i+1)+', '

		all_columns = all_columns[:-2]

		if index_fields == '':
		
			raw_query = "CREATE TABLE "+table_name+" AS ( SELECT "+all_columns+" FROM "+head_table+" t1 LEFT JOIN "+body_table+" t2 ON t1."+head_index\
					+"=t2."+body_index+" LEFT JOIN "+footer_table+" t3 ON t2."+body_index+"=t3."+footer_index+" );"

		else:
			raw_query = "CREATE TABLE "+table_name+" AS ( SELECT "+all_columns+" FROM "+head_table+" t1 LEFT JOIN "+body_table+" t2 ON t1."+head_index\
					+"=t2."+body_index+" LEFT JOIN "+footer_table+" t3 ON t2."+body_index+"=t3."+footer_index+", INDEX("+index_fields+") );"


	#------------------------------------------------------------------------#

	#------------------------ For Head and Body File -------------------------

	elif found_head and found_body and not found_foot:
		print "2nd case"

		
		for i in range(len(head_temp)):
			all_columns = all_columns+'t1.'+'c'+str(i+1)+', '
			count = count +1

		for i in range(count, count+ len(body_temp)):
			all_columns = all_columns+'t2.'+'c'+str(i+1)+', '

		all_columns = all_columns[:-2]

		if index_fields == '':

			raw_query = "CREATE TABLE "+table_name+" AS ( SELECT "+all_columns+" FROM "+head_table+" t1 LEFT JOIN "+body_table+" t2 ON t1."+head_index\
						+"=t2."+body_index+" );"

		else:
			raw_query = "CREATE TABLE "+table_name+" AS ( SELECT "+all_columns+" FROM "+head_table+" t1  LEFT JOIN "+body_table+" t2 ON t1."+head_index\
						+"=t2."+body_index+");"

		#INDEX(t1."+index_fields+")


	#-------------------------------------------------------------------------

	#------------------------ For Head and Footer File -------------------------

	elif found_head and found_foot and not found_body:
		print "3rd case"

		
		for i in range(len(head_temp)):
			all_columns = all_columns+'t1.'+'c'+str(i+1)+', '
			count = count +1

		for i in range(count, count+ len(foot_temp)):
			all_columns = all_columns+'t2.'+'c'+str(i+1)+', '

		all_columns = all_columns[:-2]

		if index_fields == '':
		
			raw_query = "CREATE TABLE "+table_name+" AS ( SELECT "+all_columns+" FROM "+head_table+" t1 LEFT JOIN "+footer_table+" t2 ON t1."+head_index\
							+"=t2."+footer_index+" );"

		else:
			raw_query = "CREATE TABLE "+table_name+" AS ( SELECT "+all_columns+" FROM "+head_table+" t1 LEFT JOIN "+footer_table+" t2 ON t1."+head_index\
							+"=t2."+footer_index+", INDEX("+index_fields+") );"

	#--------------------------------------------------------------------------#
	#------------------------ For Body and Footer File -------------------------

	elif found_body and found_foot and not found_head:
		print "4th case"


		for i in range(count, count+ len(body_temp)):
			all_columns = all_columns+'t1.'+'c'+str(i+1)+', '
			count = count +1

		for i in range(count, count+ len(foot_temp)):
			all_columns = all_columns+'t2.'+'c'+str(i+1)+', '

		all_columns = all_columns[:-2]

		if index_fields == '':

			raw_query = "CREATE TABLE "+table_name+" AS ( SELECT "+all_columns+" FROM "+body_table+" t1 LEFT JOIN "+footer_table+" t2 ON t1."+body_index\
						+"=t2."+footer_index+" );"
		else:
			raw_query = "CREATE TABLE "+table_name+" AS ( SELECT "+all_columns+" FROM "+body_table+" t1 LEFT JOIN "+footer_table+" t2 ON t1."+body_index\
						+"=t2."+footer_index+", INDEX("+index_fields+") );"

	#---------------------------------------------------------------------------#

	print raw_query

	cursor.execute(raw_query)

	if get_record.code_column_present:
		msg = alter_table(request, record_id)

	#------------------------------------------------------------------------------------------------#

	return True





@login_required
def make_raw_query(request, record_id):

	if not rc_info.objects.filter(id=record_id).exists():
		return HttpResponse("Wrong ID Provided")		

	cursor = connection.cursor()

	get_record = rc_info.objects.get(id=record_id)

	table_name = get_record.table_name

	the_file = "./media/"+str(get_record.main_file)

	temp_type = the_file.split('.')

	temp_type = temp_type[-1:]

	file_type = temp_type[0]

	print file_type


	# prepairing fields
	db_columns = get_record.database_columns

	if get_record.search_columns != None and get_record.search_columns != '':

		if str(get_record.search_columns).find('|') > -1:

			index_fields = str(get_record.search_columns).replace('|', ',')

		else:
			index_fields = str(get_record.search_columns)


	else:
		index_fields = ''

	query_fileds = ''
	
	for s in db_columns.split('|'):
		query_fileds = query_fileds+s+' varchar(255),'

	

	if index_fields != '':
		raw_query = "CREATE TABLE "+table_name+" ("+query_fileds+"INDEX("+index_fields+"));"
		
	else:
		raw_query = "CREATE TABLE "+table_name+" ("+query_fileds[:-1]+");"


	print 'mysql  started'

	# ========================= removing table if already exists ========================#

	check_query = "SHOW TABLES LIKE '"+table_name+"';"

	try:
		cursor.execute(check_query)

		check_table = cursor.fetchone();

		if len(check_table) > 0:
			delete_query = "DROP TABLE "+table_name+";"

			cursor.execute(delete_query)
	except:
		pass

	#=====================================================================================#
	print '->',raw_query
	
	cursor.execute(raw_query)

	file_type = get_record.uploaded_file_format

	header = get_record.header

	
	separator = get_record.separator

	raw_insert_query = "LOAD DATA LOCAL INFILE '"+the_file+"' INTO TABLE "+table_name+\
						" FIELDS TERMINATED BY '"+separator+"' LINES TERMINATED BY '"+"\n"+"';"

	cursor.execute(raw_insert_query)

	#=================== Altering Table ===============================

	if get_record.code_column_present:
		alter_table(request, record_id)	


	cursor.close()

	print 'mysql ends'

	return JsonResponse({'status':1, 'message':'Success'})





@login_required
def alter_table(request, record_id):
	cursor = connection.cursor()

	get_record = rc_info.objects.get(id=record_id)

	table_name = get_record.table_name

	
	if get_record.code_column_present and get_record.code_columns != None and \
						str(get_record.code_columns) != '' and str(get_record.code_columns).find('|') > -1:

		temp = ''

		code_columns = str(get_record.code_columns).split('|')


		for m in code_columns:
			temp = temp + "ADD "+m+"_c VARCHAR(100),"

		raw_query = "ALTER TABLE "+table_name+" "+temp[:-1]+" ;"

		cursor.execute(raw_query)	


		# =============== Updating code fields ============================
		code_text = get_record.code_column_text

		if code_text.find('\n') > -1:
			code_text = code_text.replace('\n', '')

		try:	

			code_fields={}

			for c in code_text.split(get_record.code_column_row_separator):
				
				temp_list = c.split(get_record.code_column_field_separator)

				code_fields[temp_list[0]] = temp_list[1]


			print 'dict values -->',code_fields.values()
			print 'dict keys -->',code_fields.keys()


			for key, value in code_fields.iteritems():

				for col in code_columns:

					raw_query = "UPDATE "+table_name+" SET "+col+"_c='"+str(value)+"' WHERE "+col+"='"+key+"';"

					print 'raw_query -->', raw_query

					cursor.execute(raw_query)
		except:

			return JsonResponse({'status':0, 'message':'Error in code text'})

		return True

	else:
		return False




#========================================= database Opration Ends =====================================#


@login_required
def example(request, record_id):
	if not rc_info.objects.filter(id=record_id).exists():
		return HttpResponse("Wrong ID Provided")		

	get_record = rc_info.objects.get(id=record_id)

	cursor = connection.cursor()

	table_name = get_record.table_name

	count_query = "SELECT COUNT(*) FROM "+table_name+";"

	cursor.execute(count_query)

	count_result = cursor.fetchall()

	count_result =count_result[0][0]

	get_record.no_of_rows = count_result

	get_record.save()

	# to get the current Database name
	db_name = connection.settings_dict['NAME']


	query =  "SELECT column_name FROM information_schema.columns WHERE table_name = '"+table_name+"' AND table_schema = '"+db_name+"';"

	print 'query -->', query

	cursor.execute(query)

	col_result = cursor.fetchall()

	print 'result -->', col_result

	all_columns = []

	for r in col_result:
		all_columns.append(r[0])

	# print all_columns

	data_query = "SELECT * FROM "+table_name+" LIMIT 10;"
	cursor.execute(data_query)

	result = cursor.fetchall()

	return render(request, 'example.html', {'all_columns':all_columns, 'result':result, 'record_id':record_id,
											'exam_id':get_record.result_id, 'total_records':count_result,})







@login_required
def view_template(request):
	if request.method == 'POST':

		if not 'exam_id' in request.POST.keys():
			return JsonResponse({"status":0, 'message':"Invalid Request Sent"})

		exam_id = request.POST['exam_id']

		if not exam_id.isdigit():
			return JsonResponse({'status':0, 'message':'Please Give Only Positive Number As Exam ID'})

		if not rc_info.objects.filter(result_id=exam_id).exists():
			return JsonResponse({'status':0, 'message':'Such record does not exists'})

		get_record = rc_info.objects.get(result_id=exam_id)

		return JsonResponse({'status':1, 'record_id':get_record.id})

	return render(request, 'view_template.html', {})






@login_required
def template(request, record_id):

	if not rc_info.objects.filter(id=record_id).exists():
		return HttpResponse("Wrong ID Provided")		

	get_record = rc_info.objects.get(id=record_id)

	table_name = get_record.table_name

	raw_query = "SELECT * FROM "+table_name+" LIMIT 12,1;"

	cursor = connection.cursor()
	cursor.execute(raw_query)

	row = cursor.fetchone()

	code_columns = []

	for c in str(get_record.code_columns).split('|'):
		code_columns.append(c+'_c')

	all_columns = str(get_record.database_columns).split('|')+code_columns

	cell_value_dict = {}

	for idx, item in enumerate(row):
		cell_value_dict[all_columns[idx]] = item
	
	print cell_value_dict

	#========================== Making design dict ========================
	design_dict = {}

	count = 0

	get_cell_info = cell_mapping.objects.filter(for_record=get_record)

	for g in get_cell_info:
		
		if str(g.value)+'_c' in code_columns:		
			design_dict[g.key] = cell_value_dict[str(g.value)+'_c']

		
		elif g.value in all_columns:
			
			design_dict[g.key] = cell_value_dict[g.value]

			count = count + 1
		else:
			design_dict[g.key] = g.value



	head_table_td, body_header_td, body_table_td, foot_table_td = create_preview_table(request, record_id, design_dict)
	

	return render(request, 'template.html', {'header_table':head_table_td, 'body_table':body_table_td, 'footer_table':foot_table_td,
											'body_header':body_header_td })






@login_required
def search(request):

	if request.method == 'POST':

		if not 'exam_id' in request.POST.keys():
			return JsonResponse({'status':0, 'message':'Invalid Id Provided'})

		exam_id = request.POST['exam_id']

		if not rc_info.objects.filter(result_id=exam_id).exists():
			return JsonResponse({'status':0, 'message':'Invalid Id Provided'})

		get_record = rc_info.objects.get(result_id=exam_id)

		return JsonResponse({'status':1, 'message':'Success', 'record_id':get_record.id})

	return render(request, 'search.html', {})





@login_required
def search_page(request, record_id):

	if not rc_info.objects.filter(id=record_id).exists():
		return JsonResponse({'status':0, 'message':'Invalid Id Provided'})

	get_record = rc_info.objects.get(id=record_id)

	search_columns = str(get_record.search_columns).split('|')

	db_columns = str(get_record.database_columns).split('|')

	prompt_columns = []

	if get_record.no_of_files_uploaded == 1:
		prompt_columns = str(get_record.innova_columns).split('|')

	else:

		if get_record.head_file != get_record.body_file and get_record.body_file != get_record.footer_file:
			
			prompt_columns = str(get_record.head_prompt).split('|')+str(get_record.body_prompt).split('|')+\
																	str(get_record.footer_prompt).split('|')

		elif get_record.head_file == get_record.body_file:
			
			prompt_columns = str(get_record.head_prompt).split('|')+str(get_record.footer_prompt).split('|')

		elif get_record.head_file == get_record.footer_file:
			
			prompt_columns = str(get_record.head_prompt).split('|')+str(get_record.body_prompt).split('|')

		elif get_record.body_file == get_record.footer_file:
			
			prompt_columns = str(get_record.head_prompt).split('|')+str(get_record.body_prompt).split('|')

	column_map = dict(zip(db_columns, prompt_columns))

	search_dict = {}


	for key in column_map.keys():

		if key in search_columns:
			search_dict[key] = column_map[key]


	#============= create searchable html ====================

	html_text = '<div>\n'

	for key in search_dict.keys():

		html_text = html_text + '<label> '+search_dict[key]+'</label> <input type="text" id="'+key+'" name="'+key+'"><p></p>'


	html_text = html_text+'</div>'



	return render(request, 'search_page.html', {'html_text':html_text, 'record_id':record_id})




@login_required
def result(request, record_id):
	if request.method == 'POST':

		query_dict = {}

		for key in request.POST.keys():
			
			if key != 'csrfmiddlewaretoken' and request.POST[key] != '':
				query_dict[key] = request.POST[key]

		if len(query_dict) == 0:
			return JsonResponse({'status':0, 'message':'You can not leave all field empty'})

		request.session['query_dict'] = query_dict

		return JsonResponse({'status':1})


	else:
		if not rc_info.objects.filter(id=record_id).exists():
			return HttpResponse("Wrong ID Provided")

		if not 'query_dict' in request.session.keys():
			return HttpResponse("Nothing Found, Please Try Again")

		query_dict = request.session['query_dict']

		get_record = rc_info.objects.get(id=record_id)

		table_name = get_record.table_name

		#----------------- Making the query -------------
		raw_query = "SELECT * FROM "+table_name+" WHERE "

		for key in query_dict.keys():

			raw_query = raw_query+key+"='"+query_dict[key]+"'"

			if len(query_dict.keys()) > 1:
				raw_query = raw_query + ' AND '

		if len(query_dict.keys()) > 1:
			raw_query = raw_query[:-5]

		raw_query = raw_query+';'

		# print raw_query
		#-------------------------------------------------

		cursor = connection.cursor()
		cursor.execute(raw_query)

		row = cursor.fetchall()

		print 'row -->', row

		# print row

		# if len(row[0]) < 1:
		# 	return JsonResponse({'status':0, 'message':'No Result Found'})


		# db_columns = str(get_record.database_columns).split('|')


		#---------------------------- To get real database columns ---------------------------------#
		# to get the current Database name
		db_name = connection.settings_dict['NAME']

		query =  "SELECT column_name FROM information_schema.columns WHERE table_name = '"+table_name+"' AND table_schema = '"+db_name+"';"

		cursor.execute(query)

		col_result = cursor.fetchall()

		db_columns = []

		for c in col_result:
			db_columns.append(c[0])

		#--------------------------- Real database columns Ends ------------------------------------#
		code_columns = []

		if get_record.code_column_present:
			code_columns = str(get_record.code_columns).split('|')


		temp_dict = {}
		
		if len(row) == 1:

			temp_dict = dict(zip(db_columns, row[0]))

		else:

			for r in row:
				for d in db_columns:
					
					if d in temp_dict.keys():
						temp_dict[d] = temp_dict[d]+[r[db_columns.index(d)]]
					else:
						temp_dict[d] = [r[db_columns.index(d)]]
			


		# print row

		print '--()',temp_dict.keys()

		#========================== Making design dict ========================
		design_dict = {}

		

		body_columns = str(get_record.body_columns).split('|')

		get_cell_info = cell_mapping.objects.filter(for_record=get_record)

		print 'still working'

		for g in get_cell_info:

			print 'still working'
			if str(g.value).find('|') > -1:
				temp = str(g.value).split('|')

				print 'got it -->', str(type(temp_dict[temp[1]]))

				if str(type(temp_dict[temp[1]])) == "<type 'list'>":
				

					if temp[1] in body_columns:

						print "I am in if part"

						count = 0

						for t in temp_dict[temp[1]]:

							if temp[1] in code_columns:
								f = temp_dict[str(temp[1])+'_c']
								t = f
								

							key_string = str(g.key).replace(str(g.key)[3:], '')
							key_no = str(int(str(g.key)[3:]) + count)

							temp_key = key_string+key_no

							design_dict[temp_key] = t
							count = count + 1

					else:
						if temp[1] in code_columns:
							
							design_dict[g.key] = temp_dict[str(temp[1])+'_c'][0]

						else:
							design_dict[g.key] = temp_dict[temp[1]][0]

				else:

					if temp[1] in code_columns:
							
						design_dict[g.key] = temp_dict[str(temp[1])+'_c']

					else:
						design_dict[g.key] = temp_dict[temp[1]]
						
	
				# else:
				# 	print "I am in else part"

				# 	if str(type(temp_dict[temp[1]])) == "<type 'list'>":

				# 		print "I am in list"
					
						

				# 	else:
				# 		print "I am in string"

						

			else:
				print "I am in last"
				design_dict[g.key] = g.value
		
		
		
		head_table_td, body_header_td, body_table_td, foot_table_td = create_multi_value_table(request, record_id, design_dict)

		finalized = get_record.finalized

		return render(request, 'result.html', {'header_table':head_table_td, 'body_table':body_table_td, 'footer_table':foot_table_td,
											'body_header':body_header_td , 'finalized':finalized, 'record_id':record_id})




@login_required
def full_final(request, record_id):

	if request.method == 'POST':

		if not rc_info.objects.filter(id=record_id).exists():
			return JsonResponse({'status':0, 'message':'Wrong Id Provided'})

		get_record = rc_info.objects.get(id=record_id)

		if request.POST['status'] == 'final':

			get_record.finalized = True

			get_record.save()

			return JsonResponse({'status':1})

		else:
			return JsonResponse({'status':0, 'message':'Wrong Keyword Found'})

	return JsonResponse({'status':0, 'message':'Access Denied'})







@login_required
def fixed_format(request):
	if request.method == 'POST':

		exam_id = request.POST['exam_id']

		if rc_info.objects.filter(result_id=exam_id).exists():
			return JsonResponse({'status':0, 'message':"Such record already exists"})

		get_record = rc_info.objects.create(result_id=exam_id, finalized_by=request.user.user)

		get_record.head_file = request.FILES['data_struct']

		get_record.body_file = request.FILES['data_file']


		get_record.table_name = 'cr'+str(exam_id)

		get_record.save()

		table_name = 'cr'+str(exam_id)


		cursor = connection.cursor()

		#=============================================================================

		data_struct = []

		count = 0

		t0 = time.time()

		# main_file = open(settings.MEDIA_ROOT+"/media/files/"+exam_id+"/main_data_file.txt", "w+")
		main_file = open("./media/files/"+exam_id+"/main_data_file.txt", "w+")

		with open("./media/"+str(get_record.head_file)) as struct_file:
			for s in struct_file:
				temp = s.replace('\r\n', '')

				temp_line = temp.split(' ')

				temp_line = filter(None, temp_line)		

				# count = count + int(temp_line[-1:][0])

				data_struct.append(temp_line[-1:][0])

		print data_struct

		fields = ''

		raw_query = ''

		start = 1

		count = 0


		for d in data_struct:

			fields = fields + 'c'+str(count+1)+" VARCHAR(255),"

			raw_query = raw_query + 'c'+str(count+1)+" = TRIM(SUBSTR(@row,"+str(start)+","+str(d)+")),"
			# raw_query = raw_query + 'c'+str(count+1)+" = SUBSTR(@row,"+str(start)+","+str(d)+"),"

			start = start + int(d)

			count = count +1


		table_query = "CREATE TABLE "+table_name+" ("+fields[:-1]+");"

		print table_query

		print "\n\n"

		cursor.execute(table_query)


		data_file = "./media/"+str(get_record.body_file)


		data_query = "LOAD DATA LOCAL INFILE '"+data_file +"' INTO TABLE "+table_name+" (@row) SET "+raw_query[:-1]+";"


		print data_query

		cursor.execute(data_query)

		ff = cursor.fetchall()

		print ff

		d = time.time() - t0

		print "duration: %.2f s." % d

		 


		return JsonResponse({'status':1})

	else:

		return render(request, 'fixed_format.html', {})


#=======================================================================================================================

