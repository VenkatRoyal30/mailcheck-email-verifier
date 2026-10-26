import logging
import uuid
from flask import Blueprint, request, jsonify, current_app
from ..database import db_session
from ..models import VerificationBatch, EmailVerification
from ..verifier.pipeline import verify_batch

logger = logging.getLogger(__name__)

verify_bp = Blueprint("verify", __name__)

@verify_bp.route("/verify", methods=["POST"])
def verify_emails():
    """
    Validates a batch of email addresses and persists the batch and records to the database.
    Payload:
    {
        "emails": ["user1@example.com", "user2@domain.org"] | "user1@example.com\nuser2@domain.org",
        "enable_smtp": false
    }
    """
    if not request.is_json:
        return jsonify({"error": "Request Content-Type must be application/json."}), 400

    data = request.get_json(silent=True)
    if not data or "emails" not in data:
        return jsonify({"error": "Missing 'emails' field in request payload."}), 400

    raw_emails_input = data["emails"]
    enable_smtp = bool(data.get("enable_smtp", current_app.config.get("ENABLE_SMTP_BY_DEFAULT", False)))

    # Parse emails: support array or multiline string
    email_list = []
    if isinstance(raw_emails_input, list):
        for item in raw_emails_input:
            if isinstance(item, str) and item.strip():
                email_list.append(item.strip())
            elif isinstance(item, str):
                # Include empty string for reporting syntax failure if intended
                email_list.append(item)
    elif isinstance(raw_emails_input, str):
        for line in raw_emails_input.splitlines():
            line_str = line.strip()
            if line_str:
                email_list.append(line_str)
    else:
        return jsonify({"error": "The 'emails' field must be an array of strings or a multiline string."}), 400

    if not email_list:
        return jsonify({"error": "Please provide at least one email address to verify."}), 400

    max_limit = current_app.config.get("MAX_BATCH_SIZE", 100)
    if len(email_list) > max_limit:
        return jsonify({
            "error": f"Batch size of {len(email_list)} exceeds maximum allowable limit of {max_limit} email addresses."
        }), 400

    dns_timeout = current_app.config.get("DNS_TIMEOUT", 3.0)
    smtp_timeout = current_app.config.get("SMTP_TIMEOUT", 5.0)
    max_retries = current_app.config.get("SMTP_MAX_RETRIES", 1)

    try:
        counts, verified_records = verify_batch(
            raw_emails=email_list,
            enable_smtp=enable_smtp,
            max_batch_size=max_limit,
            dns_timeout=dns_timeout,
            smtp_timeout=smtp_timeout,
            max_retries=max_retries
        )

        batch_id = str(uuid.uuid4())

        # Persist batch and records within transaction
        with db_session() as session:
            batch = VerificationBatch(
                id=batch_id,
                total_count=counts["total"],
                delivered_count=counts["delivered"],
                bounce_count=counts["bounce"],
                unknown_count=counts["unknown"],
                smtp_enabled=enable_smtp
            )
            session.add(batch)

            record_objs = []
            for item in verified_records:
                record = EmailVerification(
                    id=str(uuid.uuid4()),
                    batch_id=batch_id,
                    original_email=item["original_email"],
                    normalized_email=item.get("normalized_email"),
                    status=item["status"],
                    reason=item["reason"],
                    syntax_diagnostic=item.get("syntax_diagnostic"),
                    dns_diagnostic=item.get("dns_diagnostic"),
                    smtp_diagnostic=item.get("smtp_diagnostic"),
                    smtp_skipped=item.get("smtp_skipped", True)
                )
                session.add(record)
                record_objs.append(record)

            session.flush()

            # Construct response from persisted entities
            response_data = batch.to_dict(include_records=True)

        return jsonify(response_data), 201

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception("Failed during email verification batch processing")
        return jsonify({"error": "Internal verification processing error. Please try again."}), 500
