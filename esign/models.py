# models.py
from mongoengine import *

import datetime

class Student(Document):
    name = StringField(max_length=100, required=False)
    regno = StringField(max_length=50, required=True, unique=True, default="")
    email = EmailField(required=False)
    course = StringField(max_length=100, required=False)
    year = IntField(required=False)
    phone_no = StringField(max_length=15, required=False)
    password = StringField(max_length=128, required=True)
    

    def __str__(self):
        return self.regno

class Department(Document):
    name = StringField(max_length=100, required=True)
    code = StringField(max_length=10, required=True, unique=True)

    def __str__(self):
        return self.code

# Allowed field types
FIELD_TYPES = ("text", "textarea", "radio", "dropdown")

class FieldDefinition(EmbeddedDocument):
    label = StringField(required=True, max_length=200)  # e.g. "Student Name"
    type = StringField(required=True, choices=FIELD_TYPES)
    name = StringField(max_length=100)                  # machine key
    placeholder = StringField(max_length=200)
    required = BooleanField(default=False)
    options = ListField(StringField(max_length=200), default=list)  # for dropdown/radio
    order = IntField(default=0)

class FormTemplate(Document):
    title = StringField(required=True, max_length=200, unique=True)   # e.g. "Bonafide"
    issued_by = StringField(max_length=200)
    description = StringField(max_length=1000)
    fields = ListField(EmbeddedDocumentField(FieldDefinition), default=list)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.utcnow()
        return super().save(*args, **kwargs)
    
class Staff(Document):
    staffid = StringField(max_length=50, required=True, unique=True)
    name = StringField(max_length=100, required=True)
    email = EmailField(required=True, unique=True)
    password = StringField(max_length=128, required=True)
    designation = StringField(max_length=100)
    department = StringField(max_length=100)
    signature_imageurl = StringField(default="")  # always present, defaults to empty string

    def __str__(self):
        return self.staffid
