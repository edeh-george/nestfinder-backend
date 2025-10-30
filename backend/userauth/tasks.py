from logging import getLogger

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone

logger = getLogger("backend")
User = get_user_model()


@shared_task
def check_inactive_user_accounts():
    """
    Check for inactive user accounts and delete those that have been inactive for 90+ days.
    This task should be scheduled to run periodically.
    """
    inactive_users = User.inactive_objects.filter(
        deactivated_at__lte=timezone.now() - timezone.timedelta(days=90)
    )
    inactive_count = inactive_users.count()
    if inactive_count > 0:
        logger.info(
            f"Found {inactive_count} user(s) with deactivated accounts older than 90 days"
        )
        usernames_to_delete = list(inactive_users.values_list("username", flat=True))
        deletion_result = inactive_users.delete()
        logger.info(
            f"Deleted {deletion_result[0]} users: {', '.join(usernames_to_delete)}"
        )
    else:
        logger.info("No inactive users found that need deletion (>90 days)")
    remaining_inactive = User.inactive_objects.count()
    if remaining_inactive > 0:
        logger.info(
            f"There are still {remaining_inactive} inactive user accounts (less than 90 days inactive)"
        )


@shared_task(bind=True, max_retries=3, time_limit=300)
def mail_message(
    self, subject, plain_message, from_email, to, html_message, delete_on_failure=True
):
    """
    Task to send email with HTML and plain text alternatives.

    Args:
        subject: Email subject
        plain_message: Plain text version of the message
        from_email: Sender email address
        to: Recipient email address
        html_message: HTML version of the message
    """
    try:
        msg = EmailMultiAlternatives(subject, plain_message, from_email, [to])
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        return True
    except Exception as e:
        logger.error(f"Failed to send mail to {to}: {str(e)}")

        if self.request.retries >= self.max_retries:
            logger.error(f"Max retries reached for {to}. Email failed permanently.")

            if delete_on_failure and to:
                try:
                    user = User.objects.get(id=to, is_active=False)
                    user.delete()
                    logger.info(f"Deleted unverified user {to} due to email failure")
                except User.DoesNotExist:
                    logger.warning(f"User {to} not found for deletion")
        raise self.retry(exc=e, countdown=60, max_retries=3)


@shared_task
def delete_unverified_accounts():
    """

    Delete user accounts that have not verified their email for over 3 days

    """

    inactive_users = User.inactive_objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(days=3)
    )

    if inactive_users:
        logger.info(
            f"Deleting {inactive_users.count()} user(s) with unverified email addresses"
        )
        inactive_users.delete()
        logger.info("Deleted inactive accounts")
