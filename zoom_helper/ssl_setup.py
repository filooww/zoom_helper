import os
import ssl


def _build_context():
    try:
        import certifi
        ca_file = certifi.where()
        if os.path.exists(ca_file):
            os.environ["SSL_CERT_FILE"] = ca_file
            os.environ["REQUESTS_CA_BUNDLE"] = ca_file
            return ssl.create_default_context(cafile=ca_file)
    except Exception:
        pass

    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()


SSL_CTX = _build_context()
