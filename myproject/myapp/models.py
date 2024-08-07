'''
models.py
'''
from django.db.models import Max
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, signup_id, password=None, **extra_fields):
        if not signup_id:
            raise ValueError('The Signup ID field is required')
        user = self.model(signup_id=signup_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, signup_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(signup_id, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    signup_id = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    objects = UserManager()

    USERNAME_FIELD = 'signup_id'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.signup_id

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    signup_name = models.CharField(max_length=255, default='')
    phone_number = models.CharField(max_length=15)
    birth_date = models.DateField()
    sex = models.CharField(max_length=1, choices=[('남', 'Male'), ('여', 'Female')])
    address = models.CharField(max_length=255)
    detailed_address = models.CharField(max_length=255)


class Guardian(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    guardian_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    relationship = models.CharField(max_length=10, choices=[
        ('자녀', '자녀'),
        ('간병인', '간병인'),
    ])

    class Meta:
        unique_together = ('user', 'guardian_id')

    def __str__(self):
        return f'{self.name} ({self.relationship})'

    def save(self, *args, **kwargs):
        if self.guardian_id is None:
            max_id = Guardian.objects.filter(user=self.user).aggregate(Max('guardian_id'))['guardian_id__max']
            self.guardian_id = (max_id or 0) + 1
        super(Guardian, self).save(*args, **kwargs)