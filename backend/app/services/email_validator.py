import re
from typing import Tuple

# Comprehensive set of known disposable, temporary, and fake email providers
DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com", "tempmail.com", "temp-mail.org", "10minutemail.com",
    "10minutemail.net", "guerrillamail.com", "guerrillamail.net", "guerrillamail.biz",
    "sharklasers.com", "grr.la", "guerrillamailblock.com", "pokemail.net",
    "spam4.me", "yopmail.com", "yopmail.fr", "yopmail.net", "cool.fr.nf",
    "jetable.fr.nf", "courriel.fr.nf", "moncourrier.fr.nf", "monemail.fr.nf",
    "monmail.fr.nf", "getnada.com", "abcvg.com", "dropmail.me", "dispostable.com",
    "throwawaymail.com", "trashmail.com", "trashmail.net", "trashmail.me",
    "fakeinbox.com", "fakemailgenerator.com", "generator.email", "mohmal.com",
    "mytemp.email", "crazymailing.com", "burnermail.io", "emailondeck.com",
    "maildrop.cc", "inboxkitten.com", "tempail.com", "tempm.com", "nada.ltd",
    "nada.email", "getairmail.com", "chacuo.net", "trbvm.com", "crazymail.com",
    "discard.email", "discardmail.com", "spambox.us", "fastmail.fm", "mytrashmail.com",
    "incognitomail.org", "mintemail.com", "anonymbox.com", "zillamail.com",
    "trashymail.com", "spamex.com", "jetable.org", "deadaddress.com"
}

EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# Common valid TLDs and min requirements
INVALID_TLDS = {"temp", "fake", "disposable", "trash", "junk", "test", "local", "invalid"}


def validate_email_authenticity(email: str) -> Tuple[bool, str]:
    """
    Validates whether an email address is authentic, properly formatted,
    and not from a known fake / disposable email domain.
    
    Returns:
        (is_valid: bool, error_message: str)
    """
    if not email or not isinstance(email, str):
        return False, "Email address is required."

    email_clean = email.strip().lower()

    if len(email_clean) > 254 or len(email_clean) < 6:
        return False, "Email address length is invalid (must be between 6 and 254 characters)."

    if not EMAIL_REGEX.match(email_clean):
        return False, "Please enter a valid email address format (e.g. name@example.com)."

    parts = email_clean.split("@")
    if len(parts) != 2:
        return False, "Invalid email address format."

    local_part, domain = parts[0], parts[1]

    if not local_part or not domain:
        return False, "Invalid email address format."

    # Check for disposable domain
    if domain in DISPOSABLE_EMAIL_DOMAINS:
        return False, "Temporary and disposable email addresses are not permitted. Please use your genuine personal or university email (e.g. Gmail, Outlook, Yahoo)."

    # Check subdomains of disposable providers
    for disp in DISPOSABLE_EMAIL_DOMAINS:
        if domain.endswith(f".{disp}"):
            return False, "Temporary and disposable email addresses are not permitted. Please use your genuine personal or university email."

    # Check TLD validity
    domain_parts = domain.split(".")
    if len(domain_parts) < 2:
        return False, "Email domain must include a valid domain extension (e.g. .com, .org, .edu, .in)."

    tld = domain_parts[-1]
    if len(tld) < 2 or tld in INVALID_TLDS or tld.isdigit():
        return False, "Email domain contains an invalid top-level domain."

    return True, ""
