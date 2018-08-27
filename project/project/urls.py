from django.conf.urls import url, include
from django.contrib import admin
from app import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from django.conf.urls import handler404, handler500


urlpatterns = [

	url(r'^admin/', admin.site.urls),
	
	url(r'^$', views.home, name='home'),
	
	url(r'^user_login/$', views.user_login, name='user_login'),
	
	url(r'^user_logout/$', views.user_logout, name='user_logout'),

#=============================== Stage 1 =====================================
	url(r'^dashboard/$', views.dashboard, name='dashboard'),

	url(r'^replicate_record/$', views.replicate_record, name='replicate_record'),
	
	url(r'^old_parameter/(\d+)/$', views.old_parameter, name='old_parameter'),


	url(r'^data_management/$', views.data_management, name='data_management'),

	url(r'^take_parameter/(\d+)/$', views.take_parameter, name='take_parameter'),
	
	url(r'^process_parameter/$', views.process_parameter, name='process_parameter'),

	
#================================ Stage 2 =====================================

	url(r'^design_header/(\d+)/$', views.design_header, name='design_header'),
	
	url(r'^design_body/(\d+)/$', views.design_body, name='design_body'),
	
	url(r'^design_footer/(\d+)/$', views.design_footer, name='design_footer'),

	url(r'^add_records/(\d+)/$', views.add_records, name='add_records'),

	url(r'^add_design/(\d+)/$', views.add_design, name='add_design'),
	
	url(r'^reset_table/(\d+)/$', views.reset_table, name='reset_table'),
	
#================================ Stage 3 ======================================
	
	url(r'^preview/(\d+)/$', views.preview, name='preview'),

	url(r'^finalize/(\d+)/$', views.finalize, name='finalize'),

	url(r'^make_raw_query/(\d+)/$', views.make_raw_query, name='make_raw_query'),

	url(r'^example/(\d+)/$', views.example, name='example'),
#=====================================================================================

	url(r'^view_template/$', views.view_template, name='view_template'),
	
	url(r'^template/(\d+)/$', views.template, name='template'),

#========================= Searching Part ======================================

	url(r'^search/$', views.search, name='search'),

	url(r'^search_page/(\d+)/$', views.search_page, name='search_page'),

	url(r'^result/(\d+)/$', views.result, name='result'),

	url(r'^full_final/(\d+)/$', views.full_final, name='full_final'),

#================================== Other Parts ====================================#

	url(r'^fixed_format/$', views.fixed_format, name='fixed_format'),
	
	




] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#======   Error Page Section =======#

handler404 = views.error_404
handler500 = views.error_500

#===================================#
