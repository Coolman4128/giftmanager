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
            'recipient': self.owner.id,
        })

        self.assertRedirects(response, reverse('home'))
        gift = Gift.objects.get(name='New gift')
        self.assertEqual(gift.user_paired, self.owner)
        self.assertEqual(gift.created_by, self.owner)
        self.assertEqual(gift.family, self.family)
        self.assertFalse(gift.is_claimed)


class GiftForAnotherUserTests(TestCase):
    def setUp(self):
        self.family = Family.objects.create(name='Test Family', invite_code='123456')
        self.other_family = Family.objects.create(name='Other Family', invite_code='654321')
        self.creator = User.objects.create_user(
            username='creator', first_name='Casey', password='test-password', family=self.family
        )
        self.recipient = User.objects.create_user(
            username='recipient', first_name='Riley', password='test-password', family=self.family
        )
        self.family_member = User.objects.create_user(
            username='member', password='test-password', family=self.family
        )
        self.outsider = User.objects.create_user(
            username='outsider', password='test-password', family=self.other_family
        )
        self.add_url = reverse('add_gift')

    def create_gift_for_recipient(self, **overrides):
        values = {
            'name': 'A thoughtful gift',
            'description': 'Gift description',
            'link': 'https://example.com/gift',
            'family': self.family,
            'user_paired': self.recipient,
            'created_by': self.creator,
            'is_claimed': False,
        }
        values.update(overrides)
        return Gift.objects.create(**values)

    def test_add_form_lists_only_family_and_defaults_to_current_user(self):
        self.client.force_login(self.creator)

        response = self.client.get(self.add_url)

        self.assertEqual(response.status_code, 200)
        field = response.context['form'].fields['recipient']
        self.assertQuerySetEqual(
            field.queryset.order_by('id'),
            User.objects.filter(family=self.family).order_by('id'),
        )
        self.assertEqual(field.initial, self.creator)
        self.assertContains(response, 'Casey (You)')
        self.assertContains(response, 'Riley')
        self.assertNotContains(response, 'outsider')

    def test_user_can_add_gift_for_family_member(self):
        self.client.force_login(self.creator)

        response = self.client.post(self.add_url, {
            'name': 'A thoughtful gift',
            'description': 'Gift description',
            'link': '',
            'recipient': self.recipient.id,
        })

        self.assertRedirects(response, reverse('home'))
        gift = Gift.objects.get(name='A thoughtful gift')
        self.assertEqual(gift.created_by, self.creator)
        self.assertEqual(gift.user_paired, self.recipient)
        self.assertEqual(gift.family, self.family)

    def test_cross_family_recipient_is_rejected(self):
        self.client.force_login(self.creator)

        response = self.client.post(self.add_url, {
            'name': 'Invalid gift',
            'description': 'Gift description',
            'link': '',
            'recipient': self.outsider.id,
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Select a valid choice')
        self.assertFalse(Gift.objects.filter(name='Invalid gift').exists())

    def test_recipient_owns_and_can_edit_gift_without_changing_creator(self):
        gift = self.create_gift_for_recipient()
        self.client.force_login(self.recipient)

        account_response = self.client.get(reverse('account'))
        edit_response = self.client.post(reverse('edit_gift', args=[gift.id]), {
            'name': 'Updated gift',
            'description': gift.description,
            'link': gift.link,
        })

        self.assertContains(account_response, gift.name)
        self.assertContains(account_response, reverse('edit_gift', args=[gift.id]), count=2)
        self.assertRedirects(edit_response, reverse('account'))
        gift.refresh_from_db()
        self.assertEqual(gift.name, 'Updated gift')
        self.assertEqual(gift.created_by, self.creator)

    def test_recipient_can_delete_gift(self):
        gift = self.create_gift_for_recipient()
        self.client.force_login(self.recipient)

        response = self.client.post(reverse('account'), {
            'action': 'delete',
            'gift_id': gift.id,
        })

        self.assertRedirects(response, reverse('account'))
        self.assertFalse(Gift.objects.filter(id=gift.id).exists())

    def test_gift_is_not_managed_as_one_of_creators_gifts(self):
        gift = self.create_gift_for_recipient()
        self.client.force_login(self.creator)

        response = self.client.get(reverse('account'))

        self.assertNotContains(response, reverse('edit_gift', args=[gift.id]))

    def test_main_list_names_creator_in_desktop_and_mobile(self):
        gift = self.create_gift_for_recipient()
        self.client.force_login(self.family_member)

        response = self.client.get(reverse('home'))
        filtered_response = self.client.get(reverse('home'), {'filter_by': self.recipient.id})

        self.assertContains(response, '* Added by Casey', count=2)
        self.assertContains(filtered_response, '* Added by Casey', count=2)
        self.assertContains(filtered_response, gift.name)

    def test_self_created_gift_has_no_creator_message(self):
        Gift.objects.create(
            name='Self-created gift',
            description='Gift description',
            family=self.family,
            user_paired=self.recipient,
            created_by=self.recipient,
            is_claimed=False,
        )
        self.client.force_login(self.family_member)

        response = self.client.get(reverse('home'))

        self.assertNotContains(response, '* Added by')

    def test_creator_name_uses_username_fallback(self):
        self.creator.first_name = ''
        self.creator.save(update_fields=['first_name'])
        self.create_gift_for_recipient()
        self.client.force_login(self.family_member)

        response = self.client.get(reverse('home'))

        self.assertContains(response, '* Added by creator', count=2)

    def test_deleted_creator_uses_generic_fallback(self):
        gift = self.create_gift_for_recipient()
        self.creator.delete()
        gift.refresh_from_db()
        self.client.force_login(self.family_member)

        response = self.client.get(reverse('home'))

        self.assertIsNone(gift.created_by)
        self.assertContains(response, '* Added by another family member', count=2)

    def test_creator_can_claim_gift_created_for_recipient(self):
        gift = self.create_gift_for_recipient()
        self.client.force_login(self.creator)

        list_response = self.client.get(reverse('home'))
        claim_response = self.client.post(reverse('home'), {
            'action': 'claim',
            'gift_id': gift.id,
        })

        self.assertContains(list_response, gift.name)
        self.assertRedirects(claim_response, reverse('home'))
        gift.refresh_from_db()
        self.assertTrue(gift.is_claimed)
        self.assertEqual(gift.user_claimed, self.creator)

    def test_recipient_cannot_claim_own_gift_with_forged_post(self):
        gift = self.create_gift_for_recipient()
        self.client.force_login(self.recipient)

        response = self.client.post(reverse('home'), {
            'action': 'claim',
            'gift_id': gift.id,
        })

        self.assertRedirects(response, reverse('home'))
        gift.refresh_from_db()
        self.assertFalse(gift.is_claimed)
        self.assertIsNone(gift.user_claimed)

    def test_user_cannot_claim_cross_family_gift(self):
        gift = Gift.objects.create(
            name='Outsider gift',
            description='Gift description',
            family=self.other_family,
            user_paired=self.outsider,
            created_by=self.outsider,
            is_claimed=False,
        )
        self.client.force_login(self.creator)

        response = self.client.post(reverse('home'), {
            'action': 'claim',
            'gift_id': gift.id,
        })

        self.assertEqual(response.status_code, 404)
        gift.refresh_from_db()
        self.assertFalse(gift.is_claimed)
