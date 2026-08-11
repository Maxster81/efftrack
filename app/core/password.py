"""Helper per l'hashing e la verifica delle password.

Incapsula l'uso della libreria `bcrypt` direttamente (senza `passlib`,
che è abbandonato e non supporta Python 3.13+/3.14). Il formato degli
hash (`$2b$`) è identico a quello prodotto in precedenza da
`passlib.hash.bcrypt`, quindi gli hash esistenti restano validi senza
nessuna migrazione dati.

Fornisce anche la generazione di password casuali robuste
(`generate_password`) e la validazione della complessità minima
(`validate_password_complexity`), usate in creazione utente e nel
cambio password.
"""
from __future__ import annotations

import secrets
import string

import bcrypt

# Costo di default di bcrypt (rounds); 12 è il default della libreria.
_DEFAULT_ROUNDS: int = 12

# Caratteri speciali consentiti nelle password autogenerate (ASCII
# stampabili, pienamente supportati da SQLite e da bcrypt).
_SPECIAL_CHARS: str = "!@#$%&*+-.=?^"
_PASSWORD_ALPHABET: str = (
    string.ascii_uppercase + string.ascii_lowercase + string.digits + _SPECIAL_CHARS
)

# Lunghezza di default delle password autogenerate.
DEFAULT_PASSWORD_LENGTH: int = 16


def hash_password(password: str) -> str:
    """Genera l'hash bcrypt della password in chiaro (formato `$2b$`).

    Parametri:
        password: password in chiaro.

    Ritorna:
        La stringa hash pronta per la persistenza in `users.password_hash`.
    """
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=_DEFAULT_ROUNDS),
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica che la password corrisponda all'hash bcrypt memorizzato.

    Parametri:
        password: password in chiaro da verificare.
        password_hash: hash bcrypt memorizzato in `users.password_hash`.

    Ritorna:
        True se la password corrisponde, False altrimenti.
    """
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except ValueError:
        # Hash malformato o non-bcrypt: non deve mai far crashare il login.
        return False


def generate_password(length: int = DEFAULT_PASSWORD_LENGTH) -> str:
    """Genera una password casuale e robusta della lunghezza scelta.

    La password contiene tutte le classi di caratteri (maiuscole, minuscole,
    cifre e caratteri speciali) per garantire la complessità richiesta.

    Parametri:
        length: lunghezza della password (default 16).

    Ritorna:
        La password generata come stringa.
    """
    if length < 8:
        raise ValueError("La password generata deve avere almeno 8 caratteri.")

    # Garantisce almeno un carattere per ogni classe di caratteri.
    classes = [
        string.ascii_uppercase,
        string.ascii_lowercase,
        string.digits,
        _SPECIAL_CHARS,
    ]
    chars = [secrets.choice(class_set) for class_set in classes]
    # Completa con caratteri casuali dall'alfabeto completo.
    chars += [secrets.choice(_PASSWORD_ALPHABET) for _ in range(length - len(chars))]
    # Mescola per non far iniziare la password sempre con una classe fissa.
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def validate_password_complexity(password: str) -> tuple[bool, str]:
    """Verifica che la password rispetti i requisiti minimi di complessità.

    Requisiti: almeno 8 caratteri, una lettera maiuscola, una minuscola e una
    cifra. Ritorna una tupla `(ok, messaggio)`; se ok è True il messaggio è vuoto.

    Parametri:
        password: password in chiaro da validare.

    Ritorna:
        Una tupla `(bool, str)` con esito e messaggio d'errore (vuoto se ok).
    """
    if len(password) < 8:
        return False, "La password deve contenere almeno 8 caratteri."
    if not any(c.isupper() for c in password):
        return False, "La password deve contenere almeno una lettera maiuscola."
    if not any(c.islower() for c in password):
        return False, "La password deve contenere almeno una lettera minuscola."
    if not any(c.isdigit() for c in password):
        return False, "La password deve contenere almeno una cifra."
    return True, ""