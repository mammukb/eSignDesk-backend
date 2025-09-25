# esign/urls.py
from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),


    path('students/', StudentListCreate.as_view(), name='student-list-create'),
    path('students/<str:regno>/', StudentDetail.as_view(), name='student-detail'),

    # path('departments/' ,DepartmentListCreate.as_view(), name='department-list-create'),
    # path('departments/<str:code>/', DepartmentDetail.as_view(), name='department-detail'),

    path("forms/", FormTemplateListCreate.as_view()),
    path("forms/<str:form_id>/", FormTemplateDetail.as_view()),
    path("form-templates/", FormTemplateListCreate.as_view()),
    path("form-requests/", FormRequestCreateView.as_view()),

    path("staff/", StaffListCreate.as_view()),
    path("staff/<str:staffid>/", StaffDetail.as_view()),
    path("staff/request/<str:staff_id>/", StaffApprovalQueueView.as_view(), name="staff-form-requests", ),
    path("staff/request/<str:staff_id>/<str:form_id>/<str:action>/",StaffFormRequestActionView.as_view(),),

] 
