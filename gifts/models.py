from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Family(models.Model):
    name = models.CharField(max_length=200)
    invite_code = models.CharField(max_length=6)

    def __str__(self):
        return self.name

class User(AbstractUser):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.username

class Gift(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    link = models.URLField(null=True, blank=True)
    user_paired = models.ForeignKey(User, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="gifts_created",
        null=True,
    )
    user_claimed = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_claimed", null=True, blank=True)
    is_claimed = models.BooleanField()

    def __str__(self):
        return self.name

    @property
    def was_added_for_someone_else(self):
        return self.created_by_id != self.user_paired_id

    @property
    def creator_display_name(self):
        if self.created_by is None:
            return "another family member"
        return self.created_by.first_name or self.created_by.username


class Notification(models.Model):
    user_sent_to = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()

