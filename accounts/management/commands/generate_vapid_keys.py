import base64
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Generate VAPID key pair for web push notifications'

    def handle(self, *args, **options):
        try:
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.backends import default_backend
        except ImportError:
            self.stderr.write("cryptography package required: pip install cryptography")
            return

        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

        # Raw 32-byte private scalar
        private_value = private_key.private_numbers().private_value
        private_bytes = private_value.to_bytes(32, 'big')
        private_b64 = base64.urlsafe_b64encode(private_bytes).rstrip(b'=').decode()

        # Uncompressed 65-byte public key (04 + x + y)
        pub = private_key.public_key().public_numbers()
        x = pub.x.to_bytes(32, 'big')
        y = pub.y.to_bytes(32, 'big')
        public_bytes = b'\x04' + x + y
        public_b64 = base64.urlsafe_b64encode(public_bytes).rstrip(b'=').decode()

        self.stdout.write("\nAdd these to your Railway environment variables:\n")
        self.stdout.write(f"VAPID_PRIVATE_KEY={private_b64}")
        self.stdout.write(f"VAPID_PUBLIC_KEY={public_b64}")
        self.stdout.write(f"VAPID_ADMIN_EMAIL=admin@quicksave.site\n")
        self.stdout.write(self.style.SUCCESS("Done! Keep the private key secret."))
