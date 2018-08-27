from django import forms
from app.models import *
from django.contrib.auth.models import User


class file_form(forms.ModelForm):

	class Meta:

		model = rc_info
		fields = ('result_id', 'main_file')