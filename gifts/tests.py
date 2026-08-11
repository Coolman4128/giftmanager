from django.test import TestCase
from django.urls import reverse

from .models import Family, Gift, Notification, User


class EditGiftTests(TestCase):
    def setUp(self):
        self.family = Family.objects.create(name='Test Family', invite_code='123456')
        self.owner = User.objects.create_user(
            username='owner', password='test-password', family=self.family
        )
        self.claimant = User.objects.create_user(
            username='claimant', password='test-password', family=self.family
        )
        self.other_user = User.objects.create_user(
            username='other', password='test-password', family=self.family
        )
        self.gift = Gift.objects.create(
            name='Original gift',
            description='Original description',
            link='https://example.com/original',
            family=self.family,
            user_paired=self.owner,
            is_claimed=False,
        )
        self.edit_url = reverse('edit_gift', args=[self.gift.id])

    def test_edit_requires_login(self):
        response = self.client.get(self.edit_url)

        self.assertRedirects(response, f'{reverse("login")}?next={self.edit_url}')

    def test_edit_form_is_prepopulated(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Original gift')
        self.assertContains(response, 'Original description')
        self.assertContains(response, 'https://example.com/original')
        self.assertContains(response, 'Save and Close')

    def test_owner_can_edit_details_without_changing_relationships(self):
        self.gift.is_claimed = True
        self.gift.user_claimed = self.claimant
        self.gift.save()
        self.client.force_login(self.owner)

        response = self.client.post(self.edit_url, {
            'name': 'Updated gift',
            'description': 'Updated description',
            'link': 'https://example.com/updated',
        })

        self.assertRedirects(response, reverse('account'))
        self.gift.refresh_from_db()
        self.assertEqual(self.gift.name, 'Updated gift')
        self.assertEqual(self.gift.description, 'Updated description')
        self.assertEqual(self.gift.link, 'https://example.com/updated')
        self.assertEqual(self.gift.family, self.family)
        self.assertEqual(self.gift.user_paired, self.owner)
        self.assertEqual(self.gift.user_claimed, self.claimant)
        self.assertTrue(self.gift.is_claimed)

    def test_invalid_edit_does_not_modify_gift(self):
        self.client.force_login(self.owner)

        response = self.client.post(self.edit_url, {
            'name': '',
            'description': 'Changed description',
            'link': 'not-a-url',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required.')
        self.gift.refresh_from_db()
        self.assertEqual(self.gift.name, 'Original gift')
        self.assertEqual(self.gift.description, 'Original description')
        self.assertEqual(self.gift.link, 'https://example.com/original')

    def test_user_cannot_edit_another_users_gift(self):
        self.client.force_login(self.other_user)

        get_response = self.client.get(self.edit_url)
        post_response = self.client.post(self.edit_url, {
            'name': 'Unauthorized change',
            'description': 'Unauthorized change',
            'link': '',
        })

        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(post_response.status_code, 404)
        self.gift.refresh_from_db()
        self.assertEqual(self.gift.name, 'Original gift')

    def test_changed_claimed_gift_notifies_claimant(self):
        self.gift.is_claimed = True
        self.gift.user_claimed = self.claimant
        self.gift.save()
        self.client.force_login(self.owner)

        self.client.post(self.edit_url, {
            'name': 'Updated gift',
            'description': self.gift.description,
            'link': self.gift.link,
        })

        notification = Notification.objects.get(user_sent_to=self.claimant)
        self.assertEqual(notification.message, "Gift 'Updated gift' has been updated.")

    def test_unchanged_claimed_gift_does_not_notify_claimant(self):
        self.gift.is_claimed = True
        self.gift.user_claimed = self.claimant
        self.gift.save()
        self.client.force_login(self.owner)

        self.client.post(self.edit_url, {
            'name': self.gift.name,
            'description': self.gift.description,
            'link': self.gift.link,
        })

        self.assertFalse(Notification.objects.exists())

    def test_changed_unclaimed_gift_does_not_create_notification(self):
        self.client.force_login(self.owner)

        self.client.post(self.edit_url, {
            'name': 'Updated gift',
            'description': self.gift.description,
            'link': self.gift.link,
        })

        self.assertFalse(Notification.objects.exists())

    def test_account_displays_edit_link_in_desktop_and_mobile_layouts(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('account'))

        self.assertContains(response, self.edit_url, count=2)

    def test_add_gift_still_uses_form_for_new_gifts(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('add_gift'), {
            'name': 'New gift',
            'description': 'New description',
            'link': 'https://example.com/new',
        })

        self.assertRedirects(response, reverse('home'))
        gift = Gift.objects.get(name='New gift')
        self.assertEqual(gift.user_paired, self.owner)
        self.assertEqual(gift.family, self.family)
        self.assertFalse(gift.is_claimed)
