"""Streamlit UI for invoice extraction — uses the same InvoicePipeline as CLI/API."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from src.config import get_settings
from src.pipeline import InvoicePipeline

ALLOWED = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}


@st.cache_resource
def get_pipeline() -> InvoicePipeline:
    return InvoicePipeline(get_settings())


def main() -> None:
    settings = get_settings()
    st.set_page_config(page_title="Invoice Extraction", layout="wide")
    st.title("Invoice Extraction Pipeline")
    st.caption(
        f"Mode `{settings.extraction_mode}` · text `{settings.nvidia_text_model}` · "
        f"vision `{settings.nvidia_vision_model}`"
    )

    uploaded = st.file_uploader(
        "Upload invoice PDF or image",
        type=["pdf", "jpg", "jpeg", "png", "webp", "tif", "tiff", "bmp"],
    )
    if uploaded is None:
        st.info("Upload a document to extract structured invoice fields.")
        return

    suffix = Path(uploaded.name).suffix.lower()
    if suffix not in ALLOWED:
        st.error("Unsupported file type.")
        return

    col_doc, col_out = st.columns(2)
    with col_doc:
        st.subheader("Document")
        data = uploaded.getvalue()
        if suffix in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            st.image(data, use_container_width=True)
        else:
            st.write(f"**File:** `{uploaded.name}` ({len(data):,} bytes)")

    if not st.button("Extract", type="primary"):
        return

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)

    with st.spinner("Running extraction pipeline…"):
        try:
            result = get_pipeline().process(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

    with col_out:
        st.subheader("Extraction result")
        if result.status != "success" or result.invoice is None:
            st.error(f"Processing failed: `{result.error_code}` — {result.error_message}")
            st.json(
                {
                    "status": result.status,
                    "error_code": result.error_code,
                    "error_message": result.error_message,
                    "route": result.route,
                    "review": result.review,
                }
            )
            return

        inv = result.invoice
        st.success(f"Status: {result.status} · route: `{result.route}` · model: `{result.model_used}`")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Is invoice", str(inv.get("is_invoice")))
        m2.metric("Currency", inv.get("currency") or "—")
        m3.metric("Tax total", inv.get("tax_total") if inv.get("tax_total") is not None else "—")
        m4.metric("Total", inv.get("total") if inv.get("total") is not None else "—")

        st.write("**Vendor:**", inv.get("vendor"))
        st.write("**Invoice number:**", inv.get("invoice_number"))
        st.write("**Invoice date:**", inv.get("invoice_date"))

        st.subheader("Line items")
        items = inv.get("line_items")
        if items:
            st.dataframe(items, use_container_width=True)
        else:
            st.write(items)

        st.subheader("Validation")
        fin = result.financial or {}
        st.write(
            {
                "schema_valid": result.schema_valid,
                "financial_valid": fin.get("is_valid"),
                "financial_reason": fin.get("reason"),
                "expected_total": fin.get("expected_total"),
                "extracted_total": fin.get("extracted_total"),
                "difference": fin.get("difference"),
            }
        )

        st.subheader("Review")
        review = result.review or {}
        if review.get("needs_review"):
            st.warning(f"Needs review: `{review.get('review_reason')}`")
        else:
            st.info("No review flag.")

        with st.expander("Raw JSON / meta"):
            st.code(json.dumps(inv, indent=2), language="json")
            st.json(
                {
                    "route": result.route,
                    "model_used": result.model_used,
                    "latency_seconds": result.latency_seconds,
                    "cost": result.cost,
                    "notes": result.notes,
                    "review": result.review,
                }
            )


if __name__ == "__main__":
    main()
