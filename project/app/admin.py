from django.contrib import admin
from app.models import *
# Register your models here.


class user_profileAdmin(admin.ModelAdmin):
	list_display = ['first_name', 'last_name']

admin.site.register(user_profile ,user_profileAdmin)


class rc_infoAdmin(admin.ModelAdmin):
	list_display = ['id', 'result_id', 'table_name', 'no_of_rows']

admin.site.register(rc_info ,rc_infoAdmin)


class cell_mappingAdmin(admin.ModelAdmin):
	list_display = ['for_record', 'key', 'value']

admin.site.register(cell_mapping ,cell_mappingAdmin)

# class replicate_recordsAdmin(admin.ModelAdmin):
# 	list_display = ['id', 'replicated_record', 'new_record']

# admin.site.register(replicate_records ,replicate_recordsAdmin)