# esign/urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('students/', StudentListCreate.as_view(), name='student-list-create'),
    path('students/<str:regno>/', StudentDetail.as_view(), name='student-detail'),

    # path('departments/' ,DepartmentListCreate.as_view(), name='department-list-create'),
    # path('departments/<str:code>/', DepartmentDetail.as_view(), name='department-detail'),

    path("forms/", FormTemplateListCreate.as_view()),
    path("forms/<str:form_id>/", FormTemplateDetail.as_view()),

    path("staff/", StaffListCreate.as_view()),
    path("staff/<str:staffid>/", StaffDetail.as_view()),

]
