from .models import Notification


def notify(user, message, link=""):
    """
    Implements 3.3.1: 'Generate notifications to inform users of important
    recruitment activities such as successful applications, interview
    invitations, or application status updates.'
    """
    return Notification.objects.create(recipient=user, message=message, link=link)
