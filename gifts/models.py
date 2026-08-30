from django.db import models
from django.contrib.auth.models import AbstractUser

from .validators import UnlimitedURLValidator

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
    link = models.TextField(null=True, blank=True, validators=[UnlimitedURLValidator()])
    user_paired = models.ForeignKey(User, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="gifts_created",
        null=True,
    )
    user_claimed = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_claimed", null=True, blank=True)
    couple_partner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name="couple_gifts",
        null=True,
        blank=True,
    )
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

    @property
    def is_couples_gift(self):
        return self.couple_partner_id is not None

    @property
    def recipients_display_name(self):
        names = [self.user_paired.first_name or self.user_paired.username]
        if self.couple_partner_id:
            names.append(self.couple_partner.first_name or self.couple_partner.username)
        return " & ".join(names)

    def is_hidden_from(self, user):
        """A couple's gift is hidden from both people it is meant for."""
        if not self.is_couples_gift:
            return False
        return user.id in (self.user_paired_id, self.couple_partner_id)

    def can_be_managed_by(self, user):
        """Who may edit or delete this gift.

        Normally the person the gift is for manages it. A couple's gift is
        managed only by whoever created it, so neither half of the couple can
        see who claimed it.
        """
        if self.is_couples_gift:
            return self.created_by_id == user.id
        return self.user_paired_id == user.id


class Notification(models.Model):
    user_sent_to = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()

