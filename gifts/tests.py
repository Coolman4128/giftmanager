from django.test import TestCase
from django.urls import reverse

from gifts.models import Family, Gift, Notification, User


class GiftTestCase(TestCase):
    def setUp(self):
        self.family = Family.objects.create(name="Watsons", invite_code="123456")
        self.other_family = Family.objects.create(name="Others", invite_code="654321")
        self.alice = self.make_user("alice", "Alice")
        self.bob = self.make_user("bob", "Bob")
        self.carol = self.make_user("carol", "Carol")

    def make_user(self, username, first_name, family=None):
        return User.objects.create_user(
            username=username,
            password="hunter2hunter2",
            first_name=first_name,
            family=self.family if family is None else family,
        )

    def make_gift(self, recipient, creator=None, partner=None, name="Blender", **kwargs):
        return Gift.objects.create(
            name=name,
            description="A gift",
            family=self.family,
            user_paired=recipient,
            created_by=creator or recipient,
            couple_partner=partner,
            is_claimed=False,
            **kwargs,
        )


class LongLinkTests(GiftTestCase):
    def long_url(self):
        return "https://example.com/product?ref=" + ("a" * 5000)

    def test_gift_accepts_a_link_far_past_the_old_limit(self):
        self.client.force_login(self.alice)
        link = self.long_url()

        response = self.client.post(reverse('add_gift'), {
            'recipient': self.alice.id,
            'name': "Long link gift",
            'description': "A gift",
            'link': link,
        })

        self.assertRedirects(response, reverse('home'))
        self.assertEqual(Gift.objects.get(name="Long link gift").link, link)

    def test_editing_a_gift_accepts_a_long_link(self):
        gift = self.make_gift(self.alice)
        self.client.force_login(self.alice)
        link = self.long_url()

        response = self.client.post(reverse('edit_gift', args=[gift.id]), {
            'name': gift.name,
            'description': gift.description,
            'link': link,
        })

        self.assertRedirects(response, reverse('account'))
        gift.refresh_from_db()
        self.assertEqual(gift.link, link)

    def test_a_link_that_is_not_a_url_is_still_rejected(self):
        self.client.force_login(self.alice)

        response = self.client.post(reverse('add_gift'), {
            'recipient': self.alice.id,
            'name': "Bad link gift",
            'description': "A gift",
            'link': "not a url " * 100,
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Gift.objects.filter(name="Bad link gift").exists())


class CouplesGiftCreationTests(GiftTestCase):
    def post_couples_gift(self, recipient, partner, **overrides):
        data = {
            'recipient': recipient.id,
            'name': "Espresso machine",
            'description': "For the kitchen",
            'is_couples_gift': 'on',
            'couple_partner': partner.id if partner else '',
        }
        data.update(overrides)
        return self.client.post(reverse('add_gift'), data)

    def test_creating_a_couples_gift_stores_the_partner(self):
        self.client.force_login(self.alice)

        response = self.post_couples_gift(self.alice, self.bob)

        self.assertRedirects(response, reverse('home'))
        gift = Gift.objects.get(name="Espresso machine")
        self.assertEqual(gift.couple_partner, self.bob)
        self.assertTrue(gift.is_couples_gift)

    def test_creating_a_couples_gift_notifies_the_partner(self):
        self.client.force_login(self.alice)

        self.post_couples_gift(self.alice, self.bob)

        notification = Notification.objects.get(user_sent_to=self.bob)
        self.assertIn("Alice", notification.message)
        self.assertIn("Espresso machine", notification.message)
        self.assertFalse(Notification.objects.filter(user_sent_to=self.alice).exists())

    def test_unchecking_the_box_ignores_a_submitted_partner(self):
        self.client.force_login(self.alice)

        self.post_couples_gift(self.alice, self.bob, is_couples_gift='')

        gift = Gift.objects.get(name="Espresso machine")
        self.assertIsNone(gift.couple_partner)
        self.assertFalse(Notification.objects.exists())

    def test_checking_the_box_without_a_partner_is_rejected(self):
        self.client.force_login(self.alice)

        response = self.post_couples_gift(self.alice, None)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Gift.objects.exists())

    def test_the_partner_cannot_be_the_recipient(self):
        self.client.force_login(self.alice)

        response = self.post_couples_gift(self.alice, self.alice)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Gift.objects.exists())

    def test_the_partner_must_be_in_the_same_family(self):
        outsider = self.make_user("dan", "Dan", family=self.other_family)
        self.client.force_login(self.alice)

        response = self.post_couples_gift(self.alice, outsider)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Gift.objects.exists())


class CouplesGiftVisibilityTests(GiftTestCase):
    def gift_names_seen_by(self, user):
        self.client.force_login(user)
        response = self.client.get(reverse('home'))
        return [gift.name for gift in response.context['gifts']]

    def test_a_couples_gift_is_hidden_from_both_people(self):
        self.make_gift(self.alice, creator=self.alice, partner=self.bob)

        self.assertEqual(self.gift_names_seen_by(self.alice), [])
        self.assertEqual(self.gift_names_seen_by(self.bob), [])

    def test_a_couples_gift_is_visible_to_everyone_else(self):
        self.make_gift(self.alice, creator=self.alice, partner=self.bob)

        self.assertEqual(self.gift_names_seen_by(self.carol), ["Blender"])

    def test_ordinary_gifts_are_still_visible_to_the_rest_of_the_family(self):
        self.make_gift(self.alice, name="Socks")

        self.assertEqual(self.gift_names_seen_by(self.bob), ["Socks"])
        self.assertEqual(self.gift_names_seen_by(self.alice), [])

    def test_the_partner_cannot_claim_their_own_couples_gift(self):
        gift = self.make_gift(self.alice, creator=self.alice, partner=self.bob)
        self.client.force_login(self.bob)

        self.client.post(reverse('home'), {'action': 'claim', 'gift_id': gift.id})

        gift.refresh_from_db()
        self.assertFalse(gift.is_claimed)

    def test_someone_else_can_claim_a_couples_gift(self):
        gift = self.make_gift(self.alice, creator=self.alice, partner=self.bob)
        self.client.force_login(self.carol)

        self.client.post(reverse('home'), {'action': 'claim', 'gift_id': gift.id})

        gift.refresh_from_db()
        self.assertTrue(gift.is_claimed)
        self.assertEqual(gift.user_claimed, self.carol)


class CouplesGiftManagementTests(GiftTestCase):
    def account_gift_names(self, user):
        self.client.force_login(user)
        response = self.client.get(reverse('account'))
        return [gift.name for gift in response.context['attached_gifts']]

    def test_the_creator_manages_their_couples_gift(self):
        self.make_gift(self.alice, creator=self.alice, partner=self.bob)

        self.assertEqual(self.account_gift_names(self.alice), ["Blender"])
        self.assertEqual(self.account_gift_names(self.bob), [])

    def test_a_couples_gift_made_for_others_shows_only_for_its_creator(self):
        self.make_gift(self.bob, creator=self.alice, partner=self.carol)

        self.assertEqual(self.account_gift_names(self.alice), ["Blender"])
        self.assertEqual(self.account_gift_names(self.bob), [])
        self.assertEqual(self.account_gift_names(self.carol), [])

    def test_the_recipient_cannot_edit_a_couples_gift_someone_else_made(self):
        gift = self.make_gift(self.bob, creator=self.alice, partner=self.carol)
        self.client.force_login(self.bob)

        self.assertEqual(self.client.get(reverse('edit_gift', args=[gift.id])).status_code, 404)

    def test_the_partner_cannot_edit_a_couples_gift(self):
        gift = self.make_gift(self.alice, creator=self.alice, partner=self.bob)
        self.client.force_login(self.bob)

        self.assertEqual(self.client.get(reverse('edit_gift', args=[gift.id])).status_code, 404)

    def test_the_creator_can_edit_a_couples_gift(self):
        gift = self.make_gift(self.bob, creator=self.alice, partner=self.carol)
        self.client.force_login(self.alice)

        self.assertEqual(self.client.get(reverse('edit_gift', args=[gift.id])).status_code, 200)

    def test_the_recipient_cannot_delete_a_couples_gift_someone_else_made(self):
        gift = self.make_gift(self.bob, creator=self.alice, partner=self.carol)
        self.client.force_login(self.bob)

        self.client.post(reverse('account'), {'action': 'delete', 'gift_id': gift.id})

        self.assertTrue(Gift.objects.filter(id=gift.id).exists())

    def test_the_creator_can_delete_a_couples_gift(self):
        gift = self.make_gift(self.bob, creator=self.alice, partner=self.carol)
        self.client.force_login(self.alice)

        self.client.post(reverse('account'), {'action': 'delete', 'gift_id': gift.id})

        self.assertFalse(Gift.objects.filter(id=gift.id).exists())

    def test_an_ordinary_gift_is_still_managed_by_its_recipient(self):
        gift = self.make_gift(self.bob, creator=self.alice, name="Socks")

        self.assertEqual(self.account_gift_names(self.bob), ["Socks"])
        self.client.force_login(self.bob)
        self.assertEqual(self.client.get(reverse('edit_gift', args=[gift.id])).status_code, 200)


class CouplesGiftEditTests(GiftTestCase):
    def edit(self, gift, user, **overrides):
        self.client.force_login(user)
        data = {'name': gift.name, 'description': gift.description, 'link': ''}
        data.update(overrides)
        return self.client.post(reverse('edit_gift', args=[gift.id]), data)

    def test_the_edit_form_starts_checked_for_a_couples_gift(self):
        gift = self.make_gift(self.alice, creator=self.alice, partner=self.bob)
        self.client.force_login(self.alice)

        form = self.client.get(reverse('edit_gift', args=[gift.id])).context['form']

        self.assertTrue(form['is_couples_gift'].value())
        self.assertEqual(form['couple_partner'].value(), self.bob.id)

    def test_turning_an_ordinary_gift_into_a_couples_gift_notifies_the_partner(self):
        gift = self.make_gift(self.alice)

        response = self.edit(gift, self.alice, is_couples_gift='on', couple_partner=self.bob.id)

        self.assertRedirects(response, reverse('account'))
        gift.refresh_from_db()
        self.assertEqual(gift.couple_partner, self.bob)
        self.assertEqual(Notification.objects.filter(user_sent_to=self.bob).count(), 1)

    def test_changing_the_partner_notifies_only_the_new_partner(self):
        gift = self.make_gift(self.alice, creator=self.alice, partner=self.bob)

        self.edit(gift, self.alice, is_couples_gift='on', couple_partner=self.carol.id)

        gift.refresh_from_db()
        self.assertEqual(gift.couple_partner, self.carol)
        self.assertEqual(Notification.objects.filter(user_sent_to=self.carol).count(), 1)
        self.assertFalse(Notification.objects.filter(user_sent_to=self.bob).exists())

    def test_editing_other_details_does_not_re_notify_the_partner(self):
        gift = self.make_gift(self.alice, creator=self.alice, partner=self.bob)

        self.edit(gift, self.alice, name="New name", is_couples_gift='on', couple_partner=self.bob.id)

        gift.refresh_from_db()
        self.assertEqual(gift.name, "New name")
        self.assertFalse(Notification.objects.filter(user_sent_to=self.bob).exists())

    def test_unchecking_the_box_makes_the_gift_ordinary_again(self):
        gift = self.make_gift(self.alice, creator=self.alice, partner=self.bob)

        self.edit(gift, self.alice, couple_partner=self.bob.id)

        gift.refresh_from_db()
        self.assertIsNone(gift.couple_partner)
        self.assertFalse(gift.is_couples_gift)

    def test_the_partner_cannot_be_set_to_the_recipient(self):
        gift = self.make_gift(self.alice, creator=self.alice, partner=self.bob)

        response = self.edit(gift, self.alice, is_couples_gift='on', couple_partner=self.alice.id)

        self.assertEqual(response.status_code, 200)
        gift.refresh_from_db()
        self.assertEqual(gift.couple_partner, self.bob)


class GiftDisplayTests(GiftTestCase):
    def test_an_ordinary_gift_shows_one_recipient(self):
        gift = self.make_gift(self.alice)

        self.assertEqual(gift.recipients_display_name, "Alice")

    def test_a_couples_gift_shows_both_recipients(self):
        gift = self.make_gift(self.alice, creator=self.alice, partner=self.bob)

        self.assertEqual(gift.recipients_display_name, "Alice & Bob")
