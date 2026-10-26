import io
import csv
import logging
from flask import Blueprint, jsonify, Response
from ..database import db_session
from ..models import VerificationBatch, EmailVerification

logger = logging.getLogger(__name__)

history_bp = Blueprint("history", __name__)

@history_bp.route("/history", methods=["GET"])
def list_history():
    """Returns a list of previous verification batches ordered by creation date descending."""
    with db_session() as session:
        batches = (
            session.query(VerificationBatch)
            .order_by(VerificationBatch.created_at.desc())
            .all()
        )
        return jsonify({
            "count": len(batches),
            "batches": [b.to_dict(include_records=False) for b in batches]
        }), 200

@history_bp.route("/history/<batch_id>", methods=["GET"])
def get_batch_details(batch_id: str):
    """Retrieves full verification records for a specific batch."""
    with db_session() as session:
        batch = session.query(VerificationBatch).filter_by(id=batch_id).first()
        if not batch:
            return jsonify({"error": f"Verification batch '{batch_id}' not found."}), 404
        return jsonify(batch.to_dict(include_records=True)), 200

@history_bp.route("/history/<batch_id>", methods=["DELETE"])
def delete_batch(batch_id: str):
    """Deletes an entire verification batch and cascades deletion to all its records."""
    with db_session() as session:
        batch = session.query(VerificationBatch).filter_by(id=batch_id).first()
        if not batch:
            return jsonify({"error": f"Verification batch '{batch_id}' not found."}), 404
        session.delete(batch)
        return jsonify({"message": f"Verification batch '{batch_id}' successfully deleted."}), 200

@history_bp.route("/history/<batch_id>/records/<record_id>", methods=["DELETE"])
def delete_single_record(batch_id: str, record_id: str):
    """
    Deletes an individual email verification record from a batch and updates
    the batch summary counts accordingly.
    """
    with db_session() as session:
        batch = session.query(VerificationBatch).filter_by(id=batch_id).first()
        if not batch:
            return jsonify({"error": f"Verification batch '{batch_id}' not found."}), 404

        record = session.query(EmailVerification).filter_by(id=record_id, batch_id=batch_id).first()
        if not record:
            return jsonify({"error": f"Record '{record_id}' not found in batch '{batch_id}'."}), 404

        # Decrement relevant category count
        if record.status == "Likely to be delivered":
            batch.delivered_count = max(0, batch.delivered_count - 1)
        elif record.status == "Likely to bounce":
            batch.bounce_count = max(0, batch.bounce_count - 1)
        elif record.status == "Unknown":
            batch.unknown_count = max(0, batch.unknown_count - 1)

        batch.total_count = max(0, batch.total_count - 1)

        session.delete(record)
        session.flush()

        # If batch now has 0 records, optionally remove batch or keep with 0 count
        return jsonify({
            "message": f"Record '{record_id}' deleted successfully.",
            "batch": batch.to_dict(include_records=False)
        }), 200

@history_bp.route("/history", methods=["DELETE"])
def clear_all_history():
    """Clears all verification batches and records after user confirmation."""
    with db_session() as session:
        deleted_count = session.query(VerificationBatch).delete()
        return jsonify({
            "message": f"Successfully cleared all verification history ({deleted_count} batches deleted)."
        }), 200

@history_bp.route("/history/<batch_id>/export", methods=["GET"])
def export_batch_csv(batch_id: str):
    """Exports batch verification results as a downloadable CSV file."""
    with db_session() as session:
        batch = session.query(VerificationBatch).filter_by(id=batch_id).first()
        if not batch:
            return jsonify({"error": f"Verification batch '{batch_id}' not found."}), 404

        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header row
        writer.writerow([
            "Email Address",
            "Classification Status",
            "Reason",
            "Normalized Address",
            "Syntax Valid",
            "Mail Exchange (MX) Host",
            "SMTP Probed",
            "Verified At",
            "Batch ID"
        ])

        for r in batch.records:
            mx_host = "N/A"
            if r.dns_diagnostic and r.dns_diagnostic.get("mx_records"):
                mx_host = r.dns_diagnostic["mx_records"][0].get("exchange", "N/A")
            elif r.dns_diagnostic and r.dns_diagnostic.get("fallback_records"):
                mx_host = f"Fallback:{r.dns_diagnostic['fallback_records'][0].get('address', 'N/A')}"

            writer.writerow([
                r.original_email,
                r.status,
                r.reason,
                r.normalized_email or "",
                "Yes" if r.syntax_diagnostic and r.syntax_diagnostic.get("valid") else "No",
                mx_host,
                "No" if r.smtp_skipped else "Yes",
                r.created_at.isoformat() if r.created_at else "",
                batch.id
            ])

        csv_content = output.getvalue()
        filename = f"mailcheck_batch_{batch.id[:8]}_{batch.created_at.strftime('%Y%m%d_%H%M%S') if batch.created_at else 'export'}.csv"

        return Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
