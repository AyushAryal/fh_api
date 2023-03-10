from django.contrib.auth.tokens import PasswordResetTokenGenerator

from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import base36_to_int, int_to_base36
from django.conf import settings


class VerificationLinkTokenGenerator(PasswordResetTokenGenerator):
    def check_token(self, user, token):
        if not (user and token):
            return False
        try:
            ts_b36, _ = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        for secret in [self.secret, *self.secret_fallbacks]:
            if constant_time_compare(
                self.generate_token_with_timestamp(user, ts, secret),
                token,
            ):
                break
        else:
            return False

        if (self._num_seconds(self._now()) - ts) > settings.VERIFICATION_LINK_TIMEOUT:
            return False

        return True

    def make_token(self, user):
        return self.generate_token_with_timestamp(
            user,
            self._num_seconds(self._now()),
            self.secret,
        )

    def generate_token_with_timestamp(self, user, timestamp, secret):
        login_timestamp = (
            ""
            if user.last_login is None
            else user.last_login.replace(microsecond=0, tzinfo=None)
        )
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, "") or ""
        hash_value = (
            f"{user.pk}{user.password}{login_timestamp}{timestamp}"
            f"{email}{user.email_verified}"
        )

        ts_b36 = int_to_base36(timestamp)
        hash_string = salted_hmac(
            self.key_salt,
            hash_value,
            secret=secret,
            algorithm=self.algorithm,
        ).hexdigest()[::2]
        return "%s-%s" % (ts_b36, hash_string)
