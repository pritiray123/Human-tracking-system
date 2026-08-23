from __future__ import annotations
import datetime
import ipaddress
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DEFAULT_CERT_FILE = _PROJECT_ROOT / "cert.pem"
DEFAULT_KEY_FILE  = _PROJECT_ROOT / "key.pem"


def ensure_certificates(
    cert_path: Path | str = DEFAULT_CERT_FILE,
    key_path:  Path | str = DEFAULT_KEY_FILE,
    local_ip:  str | None = None,
) -> tuple[str | None, str | None]:
    cert_p = Path(cert_path)
    key_p  = Path(key_path)

    if cert_p.exists() and key_p.exists():
        return str(cert_p), str(key_p)

    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa

        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        subject_ip = local_ip or "localhost"
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, subject_ip),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "HTS Local Dev"),
        ])

        alt_names: list[x509.GeneralName] = [
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        ]

        if local_ip and local_ip != "127.0.0.1":
            try:
                alt_names.append(x509.IPAddress(ipaddress.ip_address(local_ip)))
            except ValueError:
                alt_names.append(x509.DNSName(local_ip))

        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName(alt_names),
                critical=False,
            )
            .sign(key, hashes.SHA256())
        )

        key_bytes = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
        cert_bytes = cert.public_bytes(serialization.Encoding.PEM)

        key_p.write_bytes(key_bytes)
        cert_p.write_bytes(cert_bytes)

        print(f"[Cert] Generated self-signed dev certificate:\n  Cert: {cert_p}\n  Key:  {key_p}")
        return str(cert_p), str(key_p)
    except ImportError:
        print("[Cert] cryptography package not found. Running without auto-generating certificates.")
        return None, None


if __name__ == "__main__":
    ensure_certificates()
