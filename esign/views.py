# esign/views.py
import jwt
import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Department, Student
from .serializer import *
from django.http import JsonResponse
from django.core.files.storage import default_storage  
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser

SECRET_KEY = "supersecretkey"  # 👉 move to settings.py in production

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get("email")
        password = request.data.get("password")
        role = request.data.get("role")  # "admin", "staff", "student"

        # 1. Admin authentication (hardcoded for now)
        if role == "admin" and email == "admin@gmail.com" and password == "admin":
            token = jwt.encode(
                {"email": email, "role": "admin", "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)},
                SECRET_KEY,
                algorithm="HS256"
            )
            return Response({"token": token, "role": "admin"}, status=status.HTTP_200_OK)

        # 2. Staff authentication
        if role == "staff":
            staff = Staff.objects(email=email, password=password).first()
            if staff:
                token = jwt.encode(
                    {"email": staff.email, "role": "staff", "id": str(staff.id), "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)},
                    SECRET_KEY,
                    algorithm="HS256"
                )
                return Response({"token": token, "role": "staff", "id": str(staff.id), "staffid" : str(staff.staffid)}, status=status.HTTP_200_OK)

        # 3. Student authentication
        if role == "student":
            student = Student.objects(email=email, password=password).first()
            if student:
                token = jwt.encode(
                    {"email": student.email, "role": "student", "id": str(student.id), "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=8)},
                    SECRET_KEY,
                    algorithm="HS256"
                )
                return Response({"token": token, "role": "student", "id": str(student.id), "regno":str(student.regno)}, status=status.HTTP_200_OK)

        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


def logout_view(request):
    response = JsonResponse({"message": "Logged out"})
    response.delete_cookie("jwt")   # Delete JWT cookie
    return response


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
    parser_classes = (MultiPartParser, FormParser)  # <— add this

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

        # handle file if present
        file_obj = request.FILES.get('signature_image')
        if file_obj:
            # delete old file if exists
            if staff.signature_imageurl:
                old_rel = staff.signature_imageurl.split('/media/')[-1]
                if default_storage.exists(old_rel):
                    default_storage.delete(old_rel)
            # save new file
            path = default_storage.save(f'signatures/{staffid}_{file_obj.name}', ContentFile(file_obj.read()))
            # set field so serializer picks it up
            request.data._mutable = True  # only needed if request.data is QueryDict
            request.data['signature_imageurl'] = request.build_absolute_uri('/media/' + path)

        serializer = StaffSerializer(staff, data=request.data, partial=True)
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



class FormRequestCreateView(APIView):
    def post(self, request):
        serializer = FormRequestSerializer(data=request.data)
        if serializer.is_valid():
            form_request = serializer.save()
            return Response({"id": str(form_request.id)}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from bson import ObjectId
class StaffApprovalQueueView(APIView):
    """
    GET /staff/<staff_id>/queue/
    Returns only the form requests for this staff:
      - pending for them (and all previous approvers approved)
      - skips forms already rejected by them
    """

    def get(self, request, staff_id):
        try:
            staff_obj_id = ObjectId(staff_id)
        except Exception:
            return Response({"error": "Invalid staff ID"}, status=status.HTTP_400_BAD_REQUEST)

        form_requests = FormRequest.objects(
            staff_approvals__staff_id=staff_obj_id
        )

        results = []
        for fr in form_requests:
            my_approval = None
            skip_doc = False
            show_doc = False

            for idx, approval in enumerate(fr.staff_approvals):
                if str(approval.staff_id) == staff_id:
                    if approval.status == "rejected":
                        skip_doc = True
                        break
                    elif approval.status == "pending":
                        all_prev_approved = all(
                            fr.staff_approvals[i].status == "approved"
                            for i in range(idx)
                        )
                        if all_prev_approved:
                            my_approval = approval
                            show_doc = True
                        break
                    elif approval.status == "approved":
                        break

            if skip_doc:
                continue

            if show_doc and my_approval:
                # fetch student + template docs
                student_obj = Student.objects(id=fr.student_id).first()
                template_obj = FormTemplate.objects(id=fr.template_id).first()

                # Build richer response
                results.append({
                    "form_id": str(fr.id),
                    "form_title": template_obj.title if template_obj else None,
                    "student": {
                        "id": str(student_obj.id) if student_obj else None,
                        "name": student_obj.name if student_obj else None,
                        "regno": student_obj.regno if student_obj else None,
                        "email": student_obj.email if student_obj else None,
                        "course": student_obj.course if student_obj else None,
                        "year": student_obj.year if student_obj else None,
                        "phone_no": student_obj.phone_no if student_obj else None,
                    },
                    "template": {
                        "id": str(template_obj.id) if template_obj else None,
                        "title": template_obj.title if template_obj else None,
                        "description": template_obj.description if template_obj else None,
                    },
                    "form_data": fr.form_data,
                    "my_approval": {
                        "staff_id": str(my_approval.staff_id),
                        "status": my_approval.status,
                        "remarks": my_approval.remarks,
                        "approved_at": my_approval.approved_at.isoformat() if my_approval.approved_at else None
                    }
                })

        return Response(results, status=status.HTTP_200_OK)
    

class StaffFormRequestActionView(APIView):
    """
    POST /api/staff/form-requests/<staff_id>/<form_id>/<action>/
    action = approve | reject
    """

    def post(self, request, staff_id, form_id, action):
        remark = request.data.get("remark", "")

        # validate ids
        try:
            staff_obj_id = ObjectId(staff_id)
            form_obj_id = ObjectId(form_id)
        except Exception:
            return Response({"error": "Invalid ID"}, status=status.HTTP_400_BAD_REQUEST)

        # find form
        form_request = FormRequest.objects(id=form_obj_id).first()
        if not form_request:
            return Response({"error": "Form not found"}, status=status.HTTP_404_NOT_FOUND)

        # find the staff's approval entry
        for approval in form_request.staff_approvals:
            if approval.staff_id == staff_obj_id:
                if approval.status in ["approved", "rejected"]:
                    return Response(
                        {"error": "Already processed"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                if action == "approve":
                    approval.status = "approved"
                    approval.remarks = remark
                    from datetime import datetime
                    approval.approved_at = datetime.utcnow()

                elif action == "reject":
                    approval.status = "rejected"
                    approval.remarks = remark
                    from datetime import datetime
                    approval.approved_at = datetime.utcnow()

                    # also set overall form status as rejected if needed
                    form_request.status = "rejected"

                else:
                    return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

                form_request.save()
                return Response({"message": f"{action.capitalize()}d successfully"}, status=status.HTTP_200_OK)

        return Response({"error": "Staff not in approval chain"}, status=status.HTTP_404_NOT_FOUND)