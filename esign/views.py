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

class StudentDocumentListView(APIView):
    """
    GET /api/student/<student_id>/documents/
    Returns all document (form request) details for a given student ID,
    and includes staff name for each approval entry.
    """
    def get(self, request, student_id):
        try:
            student_obj_id = ObjectId(student_id)
        except Exception:
            return Response({"error": "Invalid student ID"}, status=status.HTTP_400_BAD_REQUEST)

        # fetch student details (may be None)
        student_obj = Student.objects(id=student_obj_id).first()

        form_requests = FormRequest.objects(student_id=student_obj_id)
        if not form_requests:
            return Response({"message": "No documents found"}, status=status.HTTP_404_NOT_FOUND)

        documents = []
        for form in form_requests:
            template = None
            if getattr(form, "template_id", None):
                template = FormTemplate.objects(id=form.template_id).first()

            staff_approvals = []
            for a in getattr(form, "staff_approvals", []):
                staff_obj = None
                if getattr(a, "staff_id", None):
                    staff_obj = Staff.objects(id=a.staff_id).first()

                # build full staff info when available
                staff_info = None
                if staff_obj:
                    staff_info = {
                        "id": str(staff_obj.id),
                        "staffid": getattr(staff_obj, "staffid", None),
                        "name": getattr(staff_obj, "name", None),
                        "email": getattr(staff_obj, "email", None),
                        "designation": getattr(staff_obj, "designation", None),
                        "department": getattr(staff_obj, "department", None),
                        "signature_imageurl": getattr(staff_obj, "signature_imageurl", None),
                    }

                staff_approvals.append({
                    "staff_id": str(a.staff_id) if getattr(a, "staff_id", None) else None,
                    "staff": staff_info,
                    "status": getattr(a, "status", None),
                    "remarks": getattr(a, "remarks", None),
                    "approved_at": a.approved_at.isoformat() if getattr(a, "approved_at", None) else None
                })

            # prefer submitted_at if present, else fallback to created_at
            submitted_at = None
            if getattr(form, "submitted_at", None):
                submitted_at = form.submitted_at.isoformat()
            elif getattr(form, "created_at", None):
                submitted_at = form.created_at.isoformat()

            documents.append({
                "form_id": str(form.id),
                "template": {
                    "id": str(template.id) if template else None,
                    "title": getattr(template, "title", None),
                    "issued_by": getattr(template, "issued_by", None),
                    "description": getattr(template, "description", None),
                },
                "student": {
                    "id": str(student_obj.id) if student_obj else None,
                    "regno": getattr(student_obj, "regno", None),
                    "name": getattr(student_obj, "name", None),
                    "email": getattr(student_obj, "email", None),
                    "course": getattr(student_obj, "course", None),
                    "year": getattr(student_obj, "year", None),
                    "phone_no": getattr(student_obj, "phone_no", None),
                },
                "status": getattr(form, "status", None),
                "submitted_at": submitted_at,
                "form_data": getattr(form, "form_data", None),
                "staff_approvals": staff_approvals
            })

        return Response({"documents": documents}, status=status.HTTP_200_OK)



class StaffDocumentListView(APIView):
    """
    GET /api/staff/<staff_id>/documents/
    Returns all documents approved or rejected by a specific staff member.
    """

    def get(self, request, staff_id):
        try:
            staff_obj_id = ObjectId(staff_id)
        except Exception:
            return Response({"error": "Invalid staff ID"}, status=status.HTTP_400_BAD_REQUEST)

        staff_obj = Staff.objects(id=staff_obj_id).first()
        if not staff_obj:
            return Response({"error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)

        # Fetch all forms where this staff is part of staff_approvals
        form_requests = FormRequest.objects(staff_approvals__staff_id=staff_obj_id)
        if not form_requests:
            return Response({"message": "No documents found for this staff"}, status=status.HTTP_404_NOT_FOUND)

        documents = []
        for form in form_requests:
            # Find this staff member’s approval entry
            staff_approval_entry = None
            for a in getattr(form, "staff_approvals", []):
                if str(a.staff_id) == str(staff_obj_id):
                    if getattr(a, "status", None) in ["approved", "rejected"]:  # ✅ filter here
                        staff_approval_entry = a
                    break

            # Skip if staff hasn't yet approved/rejected
            if not staff_approval_entry:
                continue

            # Load related details
            student_obj = Student.objects(id=form.student_id).first() if getattr(form, "student_id", None) else None
            template_obj = FormTemplate.objects(id=form.template_id).first() if getattr(form, "template_id", None) else None

            submitted_at = (
                form.submitted_at.isoformat()
                if getattr(form, "submitted_at", None)
                else form.created_at.isoformat() if getattr(form, "created_at", None) else None
            )

            documents.append({
                "form_id": str(form.id),
                "template": {
                    "id": str(template_obj.id) if template_obj else None,
                    "title": getattr(template_obj, "title", None),
                    "issued_by": getattr(template_obj, "issued_by", None),
                    "description": getattr(template_obj, "description", None),
                },
                "student": {
                    "id": str(student_obj.id) if student_obj else None,
                    "regno": getattr(student_obj, "regno", None),
                    "name": getattr(student_obj, "name", None),
                    "email": getattr(student_obj, "email", None),
                    "course": getattr(student_obj, "course", None),
                    "year": getattr(student_obj, "year", None),
                    "phone_no": getattr(student_obj, "phone_no", None),
                },
                "status": getattr(form, "status", None),
                "submitted_at": submitted_at,
                "form_data": getattr(form, "form_data", None),
                "staff_decision": {
                    "status": getattr(staff_approval_entry, "status", None),
                    "remarks": getattr(staff_approval_entry, "remarks", None),
                    "approved_at": staff_approval_entry.approved_at.isoformat() if getattr(staff_approval_entry, "approved_at", None) else None,
                }
            })

        if not documents:
            return Response({"message": "No approved or rejected documents found"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"documents": documents}, status=status.HTTP_200_OK)

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

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class StaffDetail(APIView):
    # parser_classes = (MultiPartParser, FormParser)  # <— add this
    parser_classes = [MultiPartParser, FormParser, JSONParser]

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

    # def put(self, request, staffid):
    #     staff = self.get_object(staffid)
    #     if not staff:
    #         return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    #     # handle file if present
    #     file_obj = request.FILES.get('signature_image')
    #     if file_obj:
    #         # delete old file if exists
    #         if staff.signature_imageurl:
    #             old_rel = staff.signature_imageurl.split('/media/')[-1]
    #             if default_storage.exists(old_rel):
    #                 default_storage.delete(old_rel)
    #         # save new file
    #         path = default_storage.save(f'signatures/{staffid}_{file_obj.name}', ContentFile(file_obj.read()))
    #         # set field so serializer picks it up
    #         request.data._mutable = True  # only needed if request.data is QueryDict
    #         request.data['signature_imageurl'] = request.build_absolute_uri('/media/' + path)

    #     serializer = StaffSerializer(staff, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request, staffid):
        staff = self.get_object(staffid)
        if not staff:
            return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        # ⬇️ NEW: Only handle file if it's present
        file_obj = request.FILES.get('signature_image')
        if file_obj:
            # delete old file if exists (unchanged)
            if staff.signature_imageurl:
                old_rel = staff.signature_imageurl.split('/media/')[-1]
                if default_storage.exists(old_rel):
                    default_storage.delete(old_rel)
            # save new file (unchanged)
            path = default_storage.save(
                f'signatures/{staffid}_{file_obj.name}',
                ContentFile(file_obj.read())
            )
            # ⬇️ NEW: make request.data mutable only if needed
            if hasattr(request.data, "_mutable"):
                request.data._mutable = True
            request.data['signature_imageurl'] = request.build_absolute_uri('/media/' + path)

        # serializer & save (same as before)
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


class FormRequestDetail(APIView):
    """
    DELETE /form-requests/<form_id>/
    Delete a FormRequest by its ObjectId string.
    """
    def delete(self, request, form_id):
        try:
            form_obj_id = ObjectId(form_id)
        except Exception:
            return Response({"error": "Invalid form id"}, status=status.HTTP_400_BAD_REQUEST)

        form_request = FormRequest.objects(id=form_obj_id).first()
        if not form_request:
            return Response({"error": "FormRequest not found"}, status=status.HTTP_404_NOT_FOUND)

        # perform delete
        form_request.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
                
                student_obj = Student.objects(id=fr.student_id).first()
                template_obj = FormTemplate.objects(id=fr.template_id).first()

                
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
    

# class StaffFormRequestActionView(APIView):
#     """
#     POST /api/staff/form-requests/<staff_id>/<form_id>/<action>/
#     action = approve | reject
#     """

#     def post(self, request, staff_id, form_id, action):
#         remark = request.data.get("remark", "")

#         # validate ids
#         try:
#             staff_obj_id = ObjectId(staff_id)
#             form_obj_id = ObjectId(form_id)
#         except Exception:
#             return Response({"error": "Invalid ID"}, status=status.HTTP_400_BAD_REQUEST)

#         # find form
#         form_request = FormRequest.objects(id=form_obj_id).first()
#         if not form_request:
#             return Response({"error": "Form not found"}, status=status.HTTP_404_NOT_FOUND)

#         # find the staff's approval entry
#         for approval in form_request.staff_approvals:
#             if approval.staff_id == staff_obj_id:
#                 if approval.status in ["approved", "rejected"]:
#                     return Response(
#                         {"error": "Already processed"},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )

#                 if action == "approve":
#                     approval.status = "approved"
#                     approval.remarks = remark
#                     from datetime import datetime
#                     approval.approved_at = datetime.utcnow()

#                 elif action == "reject":
#                     approval.status = "rejected"
#                     approval.remarks = remark
#                     from datetime import datetime
#                     approval.approved_at = datetime.utcnow()

#                     # also set overall form status as rejected if needed
#                     form_request.status = "rejected"

#                 else:
#                     return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

#                 form_request.save()
#                 return Response({"message": f"{action.capitalize()}d successfully"}, status=status.HTTP_200_OK)

#         return Response({"error": "Staff not in approval chain"}, status=status.HTTP_404_NOT_FOUND)



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

                from datetime import datetime

                if action == "approve":
                    approval.status = "approved"
                    approval.remarks = remark
                    approval.approved_at = datetime.utcnow()

                elif action == "reject":
                    approval.status = "rejected"
                    approval.remarks = remark
                    approval.approved_at = datetime.utcnow()
                    # If anyone rejects, the whole form is rejected
                    form_request.status = "rejected"

                else:
                    return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)

                # Check if all staff have approved
                if action == "approve":
                    all_approved = all(
                        a.status == "approved" for a in form_request.staff_approvals
                    )
                    if all_approved:
                        form_request.status = "approved"

                form_request.save()
                return Response({"message": f"{action.capitalize()}d successfully"}, status=status.HTTP_200_OK)

        return Response({"error": "Staff not in approval chain"}, status=status.HTTP_404_NOT_FOUND)


class FormStdDetails(APIView):
    """
    GET /api/forms/student/<std_id>/
    Returns all forms for a given student ID
    """

    def get(self, request, std_id):
        # Validate student ID
        try:
            student_obj_id = ObjectId(std_id)
        except Exception:
            return Response({"error": "Invalid student ID"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch all form requests for this student
        form_requests = FormRequest.objects(student_id=student_obj_id)

        # if not form_requests:
        #     return Response({"message": "No forms found"}, status=status.HTTP_404_NOT_FOUND)

        # Prepare response
        result = []
        for form in form_requests:
            form_data = {
                "form_id": str(form.id),
                "template_id": str(form.template.id) if hasattr(form, 'template') else None,
                "template_name": form.template.name if hasattr(form, 'template') else None,
                "status": form.status,
                "submitted_at": form.submitted_at.isoformat() if hasattr(form, 'submitted_at') else None,
                "staff_approvals": [
                    {
                        "staff_id": str(a.staff_id),
                        "status": a.status,
                        "remarks": a.remarks,
                        "approved_at": a.approved_at.isoformat() if hasattr(a, 'approved_at') and a.approved_at else None
                    }
                    for a in form.staff_approvals
                ]
            }
            result.append(form_data)

        return Response({"forms": result}, status=status.HTTP_200_OK)
