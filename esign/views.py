# esign/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Department, Student
from .serializer import *

class StudentListCreate(APIView):
    def get(self, request):
        students = Student.objects()
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            student = serializer.save()
            return Response(StudentSerializer(student).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentDetail(APIView):
    def get_object(self, regno):
        try:
            return Student.objects.get(regno=regno)
        except Student.DoesNotExist:
            return None

    def get(self, request, regno):
        student = self.get_object(regno)
        if not student:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentSerializer(student)
        return Response(serializer.data)

    def put(self, request, regno):
        student = self.get_object(regno)
        if not student:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = StudentSerializer(student, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, regno):
        student = self.get_object(regno)
        if not student:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        student.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
# class DepartmentListCreate(APIView):
#     def get(self, request):
#         departments = Department.objects()
#         serializer = DepartmentSerializer(departments, many=True)
#         return Response(serializer.data)

#     def post(self, request):
#         serializer = DepartmentSerializer(data=request.data)
#         if serializer.is_valid():
#             department = serializer.save()
#             return Response(DepartmentSerializer(department).data, status=status.HTTP_201_CREATED)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# class DepartmentDetail(APIView):
#     def get_object(self, code):
#         try:
#             return Department.objects.get(code=code)
#         except Department.DoesNotExist:
#             return None

#     def get(self, request, code):
#         department = self.get_object(code)
#         if not department:
#             return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
#         serializer = DepartmentSerializer(department)
#         return Response(serializer.data)
    
#     def put(self, request, code):
#         department = self.get_object(code)
#         if not department:
#             return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
#         serializer = DepartmentSerializer(department, data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response(serializer.data)
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     def delete(self, request, code):
#         department = self.get_object(code)
#         if not department:
#             return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
#         department.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
    
# --- Form Templates ---
class FormTemplateListCreate(APIView):
    def get(self, request):
        forms = FormTemplate.objects()
        serializer = FormTemplateSerializer(forms, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = FormTemplateSerializer(data=request.data)
        if serializer.is_valid():
            form = serializer.save()
            return Response(FormTemplateSerializer(form).data, status=201)
        return Response(serializer.errors, status=400)

class FormTemplateDetail(APIView):
    def get_object(self, form_id):
        return FormTemplate.objects(id=form_id).first()

    def get(self, request, form_id):
        form = self.get_object(form_id)
        if not form:
            return Response({"error": "Not found"}, status=404)
        return Response(FormTemplateSerializer(form).data)

    def put(self, request, form_id):
        form = self.get_object(form_id)
        if not form:
            return Response({"error": "Not found"}, status=404)
        serializer = FormTemplateSerializer(form, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, form_id):
        form = self.get_object(form_id)
        if not form:
            return Response({"error": "Not found"}, status=404)
        form.delete()
        return Response(status=204)


# --- End Form Templates ---

#staff views here

class StaffListCreate(APIView):
    def get(self, request):
        staff = Staff.objects()
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StaffSerializer(data=request.data)
        if serializer.is_valid():
            staff = serializer.save()
            return Response(StaffSerializer(staff).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDetail(APIView):
    def get_object(self, staffid):
        try:
            return Staff.objects.get(staffid=staffid)
        except Staff.DoesNotExist:
            return None

    def get(self, request, staffid):
        staff = self.get_object(staffid)
        if not staff:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(StaffSerializer(staff).data)

    def put(self, request, staffid):
        staff = self.get_object(staffid)
        if not staff:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = StaffSerializer(staff, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, staffid):
        staff = self.get_object(staffid)
        if not staff:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        staff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
# --- End Staff ---