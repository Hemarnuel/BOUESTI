from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class RecruiterApprovalTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_user(
			username="reviewer",
			password="Test-pass-12345",
			role=User.Role.ADMIN,
		)

	def register(self, role, username):
		return self.client.post(
			reverse("accounts:register"),
			{
				"first_name": "Taylor",
				"last_name": "Recruiter",
				"username": username,
				"email": f"{username}@example.com",
				"phone_number": "555-0100",
				"role": role,
				"password1": "S3cure-test-password!",
				"password2": "S3cure-test-password!",
			},
		)

	def test_recruiter_signup_waits_for_admin_review(self):
		response = self.register(User.Role.RECRUITER, "new-recruiter")

		recruiter = User.objects.get(username="new-recruiter")
		self.assertRedirects(response, reverse("accounts:login"))
		self.assertFalse(recruiter.is_active)
		self.assertEqual(recruiter.recruiter_approval, User.RecruiterApproval.PENDING)
		self.assertNotIn("_auth_user_id", self.client.session)

	def test_applicant_signup_remains_immediate(self):
		response = self.register(User.Role.APPLICANT, "new-applicant")

		applicant = User.objects.get(username="new-applicant")
		self.assertRedirects(response, reverse("recruitment:dashboard"))
		self.assertTrue(applicant.is_active)
		self.assertIn("_auth_user_id", self.client.session)

	def test_admin_can_approve_pending_recruiter(self):
		recruiter = User.objects.create_user(
			username="pending",
			password="Test-pass-12345",
			role=User.Role.RECRUITER,
			is_active=False,
			recruiter_approval=User.RecruiterApproval.PENDING,
		)
		self.client.force_login(self.admin)

		response = self.client.post(
			reverse("recruitment:admin_review_recruiter", args=[recruiter.pk]),
			{"decision": User.RecruiterApproval.APPROVED},
		)

		recruiter.refresh_from_db()
		self.assertRedirects(response, reverse("recruitment:admin_recruiter_approvals"))
		self.assertEqual(recruiter.recruiter_approval, User.RecruiterApproval.APPROVED)
		self.assertTrue(recruiter.is_active)
		self.assertEqual(recruiter.recruiter_reviewed_by, self.admin)
		self.assertIsNotNone(recruiter.recruiter_reviewed_at)

	def test_admin_can_reject_and_keep_recruiter_inactive(self):
		recruiter = User.objects.create_user(
			username="declined",
			password="Test-pass-12345",
			role=User.Role.RECRUITER,
			is_active=False,
			recruiter_approval=User.RecruiterApproval.PENDING,
		)
		self.client.force_login(self.admin)

		self.client.post(
			reverse("recruitment:admin_review_recruiter", args=[recruiter.pk]),
			{"decision": User.RecruiterApproval.REJECTED},
		)

		recruiter.refresh_from_db()
		self.assertEqual(recruiter.recruiter_approval, User.RecruiterApproval.REJECTED)
		self.assertFalse(recruiter.is_active)

	def test_non_admin_cannot_open_approval_queue(self):
		applicant = User.objects.create_user(
			username="applicant",
			password="Test-pass-12345",
			role=User.Role.APPLICANT,
		)
		self.client.force_login(applicant)

		response = self.client.get(reverse("recruitment:admin_recruiter_approvals"))

		self.assertRedirects(response, reverse("recruitment:dashboard"))

	def test_admin_queue_lists_pending_recruiters(self):
		recruiter = User.objects.create_user(
			username="queue-candidate",
			password="Test-pass-12345",
			role=User.Role.RECRUITER,
			is_active=False,
			recruiter_approval=User.RecruiterApproval.PENDING,
		)
		self.client.force_login(self.admin)

		response = self.client.get(reverse("recruitment:admin_recruiter_approvals"))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, recruiter.username)
		self.assertContains(response, "Approve")
		self.assertContains(response, "Reject")

	def test_admin_user_toggle_cannot_activate_unapproved_recruiter(self):
		recruiter = User.objects.create_user(
			username="still-pending",
			password="Test-pass-12345",
			role=User.Role.RECRUITER,
			is_active=False,
			recruiter_approval=User.RecruiterApproval.PENDING,
		)
		self.client.force_login(self.admin)

		self.client.post(reverse("recruitment:admin_toggle_user", args=[recruiter.pk]))

		recruiter.refresh_from_db()
		self.assertFalse(recruiter.is_active)
		self.assertEqual(recruiter.recruiter_approval, User.RecruiterApproval.PENDING)
