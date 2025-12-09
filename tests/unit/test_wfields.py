import base64
import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from document_utils import DocumentKind
from wfields import (
    extract_item_data,
    get_document_items,
    get_item_article_number,
    get_item_description,
    get_supplier_ids,
    unpack_attachments,
)


class TestUnpackAttachments:
    """Test the unpack_attachments function."""

    def test_unpack_interpreted_data_json(self):
        """Test unpacking interpreted_data.json attachment."""
        data = {"supplier": "Test Supplier", "amount": 100}
        encoded = base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")
        doc = {
            "attachments": [
                {"name": "interpreted_data.json", "value": encoded}
            ]
        }

        unpack_attachments(doc)

        assert "interpreted_data" in doc
        assert doc["interpreted_data"] == data

    def test_unpack_interpreted_xml_json(self):
        """Test unpacking interpreted_xml.json attachment."""
        data = {"xml_field": "Test Data", "value": 200}
        encoded = base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")
        doc = {
            "attachments": [
                {"name": "interpreted_xml.json", "value": encoded}
            ]
        }

        unpack_attachments(doc)

        assert "interpreted_xml" in doc
        assert doc["interpreted_xml"] == data

    def test_unpack_case_insensitive(self):
        """Test that attachment names are case-insensitive."""
        data = {"test": "data"}
        encoded = base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")
        doc = {
            "attachments": [
                {"name": "INTERPRETED_DATA.JSON", "value": encoded}
            ]
        }

        unpack_attachments(doc)

        assert "interpreted_data" in doc
        assert doc["interpreted_data"] == data

    def test_skip_pdf_attachments(self):
        """Test that PDF attachments are ignored."""
        doc = {
            "attachments": [
                {"name": "document.pdf", "value": "base64data"}
            ]
        }

        unpack_attachments(doc)

        # Should not add any new fields
        assert "interpreted_data" not in doc
        assert "interpreted_xml" not in doc

    def test_dont_overwrite_existing_interpreted_data(self):
        """Test that existing interpreted_data is not overwritten."""
        existing_data = {"existing": "data"}
        new_data = {"new": "data"}
        encoded = base64.b64encode(json.dumps(new_data).encode("utf-8")).decode("utf-8")
        doc = {
            "interpreted_data": existing_data,
            "attachments": [
                {"name": "interpreted_data.json", "value": encoded}
            ]
        }

        unpack_attachments(doc)

        assert doc["interpreted_data"] == existing_data

    def test_handle_invalid_base64(self, caplog):
        """Test handling of invalid base64 data."""
        doc = {
            "attachments": [
                {"name": "interpreted_data.json", "value": "invalid!!!base64"}
            ]
        }

        with caplog.at_level(logging.ERROR):
            unpack_attachments(doc)

        assert "interpreted_data" not in doc
        assert "Failed to decode interpreted_data.json" in caplog.text

    def test_handle_invalid_json(self, caplog):
        """Test handling of invalid JSON data."""
        invalid_json = "not json"
        encoded = base64.b64encode(invalid_json.encode("utf-8")).decode("utf-8")
        doc = {
            "attachments": [
                {"name": "interpreted_data.json", "value": encoded}
            ]
        }

        with caplog.at_level(logging.ERROR):
            unpack_attachments(doc)

        assert "interpreted_data" not in doc
        assert "Failed to decode interpreted_data.json" in caplog.text

    def test_no_attachments(self):
        """Test document with no attachments."""
        doc = {}

        unpack_attachments(doc)

        assert "interpreted_data" not in doc
        assert "interpreted_xml" not in doc

    def test_empty_attachments_list(self):
        """Test document with empty attachments list."""
        doc = {"attachments": []}

        unpack_attachments(doc)

        assert "interpreted_data" not in doc
        assert "interpreted_xml" not in doc


class TestGetSupplierIds:
    """Test the get_supplier_ids function."""

    def test_get_supplier_ids_from_headers(self):
        """Test extracting supplier IDs from document headers."""
        doc = {
            "headers": [
                {"name": "supplierId", "value": "SUP-001"},
                {"name": "bankgiro", "value": "123-4567"},
            ]
        }

        ids = get_supplier_ids(doc)

        assert "SUP-001" in ids
        assert "123-4567" in ids

    def test_get_supplier_ids_from_interpreted_data(self):
        """Test extracting supplier ID from interpreted_data."""
        doc = {
            "interpreted_data": {
                "supplierId": "SUP-INT-001"
            }
        }

        ids = get_supplier_ids(doc)

        assert "SUP-INT-001" in ids

    def test_get_all_supplier_id_fields(self):
        """Test that all supplier ID field names are checked."""
        doc = {
            "headers": [
                {"name": "supplierId", "value": "SUP-001"},
                {"name": "supplierExternalId", "value": "EXT-001"},
                {"name": "supplierInternalId", "value": "INT-001"},
                {"name": "supplierIncomingId", "value": "INC-001"},
                {"name": "bankgiro", "value": "123-4567"},
            ],
            "interpreted_data": {
                "supplierId": "SUP-INT-001"
            }
        }

        ids = get_supplier_ids(doc)

        assert len(ids) == 6
        assert "SUP-001" in ids
        assert "EXT-001" in ids
        assert "INT-001" in ids
        assert "INC-001" in ids
        assert "123-4567" in ids
        assert "SUP-INT-001" in ids

    def test_get_supplier_ids_empty_doc(self):
        """Test with empty document."""
        doc = {}

        ids = get_supplier_ids(doc)

        assert ids == []

    def test_get_supplier_ids_no_matches(self):
        """Test with document that has no supplier IDs."""
        doc = {
            "headers": [
                {"name": "invoiceNumber", "value": "INV-001"},
            ]
        }

        ids = get_supplier_ids(doc)

        assert ids == []

    def test_get_supplier_ids_deduplication(self):
        """Test that duplicate supplier IDs are included."""
        doc = {
            "headers": [
                {"name": "supplierId", "value": "SUP-001"},
            ],
            "interpreted_data": {
                "supplierId": "SUP-001"
            }
        }

        ids = get_supplier_ids(doc)

        # Both instances should be in the list
        assert ids.count("SUP-001") == 2


class TestGetItemDescription:
    """Test the get_item_description function."""

    def test_get_inventory_description(self):
        """Test getting inventoryDescription field."""
        item = {
            "fields": [
                {"name": "inventoryDescription", "value": "Widget A"}
            ]
        }

        desc = get_item_description(item)

        assert desc == "Widget A"

    def test_get_description_field(self):
        """Test getting description field."""
        item = {
            "fields": [
                {"name": "description", "value": "Service B"}
            ]
        }

        desc = get_item_description(item)

        assert desc == "Service B"

    def test_get_text_field(self):
        """Test getting text field."""
        item = {
            "fields": [
                {"name": "text", "value": "Product C"}
            ]
        }

        desc = get_item_description(item)

        assert desc == "Product C"

    def test_priority_order(self):
        """Test that inventoryDescription has priority over others."""
        item = {
            "fields": [
                {"name": "text", "value": "Text Field"},
                {"name": "description", "value": "Description Field"},
                {"name": "inventoryDescription", "value": "Inventory Field"},
            ]
        }

        desc = get_item_description(item)

        assert desc == "Inventory Field"

    def test_fallback_to_description(self):
        """Test fallback from inventoryDescription to description."""
        item = {
            "fields": [
                {"name": "description", "value": "Description Field"},
                {"name": "text", "value": "Text Field"},
            ]
        }

        desc = get_item_description(item)

        assert desc == "Description Field"

    def test_fallback_to_text(self):
        """Test fallback to text when others are missing."""
        item = {
            "fields": [
                {"name": "text", "value": "Text Field"},
            ]
        }

        desc = get_item_description(item)

        assert desc == "Text Field"

    def test_no_description_fields(self):
        """Test when no description fields exist."""
        item = {
            "fields": [
                {"name": "lineNumber", "value": "1"},
            ]
        }

        desc = get_item_description(item)

        assert desc is None


class TestGetItemArticleNumber:
    """Test the get_item_article_number function."""

    def test_get_inventory_number(self):
        """Test getting inventoryNumber field."""
        item = {
            "fields": [
                {"name": "inventoryNumber", "value": "INV-001"}
            ]
        }

        num = get_item_article_number(item)

        assert num == "INV-001"

    def test_get_inventory_field(self):
        """Test getting inventory field."""
        item = {
            "fields": [
                {"name": "inventory", "value": "INV-002"}
            ]
        }

        num = get_item_article_number(item)

        assert num == "INV-002"

    def test_priority_order(self):
        """Test that inventoryNumber has priority over inventory."""
        item = {
            "fields": [
                {"name": "inventory", "value": "INV-002"},
                {"name": "inventoryNumber", "value": "INV-001"},
            ]
        }

        num = get_item_article_number(item)

        assert num == "INV-001"

    def test_no_article_number(self):
        """Test when no article number fields exist."""
        item = {
            "fields": [
                {"name": "description", "value": "Some item"},
            ]
        }

        num = get_item_article_number(item)

        assert num is None


class TestExtractItemData:
    """Test the extract_item_data function."""

    def test_extract_purchase_order_item(self):
        """Test extracting data from purchase order item."""
        item = {
            "fields": [
                {"name": "lineNumber", "value": "1"},
                {"name": "description", "value": "Widget A"},
                {"name": "unitAmount", "value": "10.50"},
                {"name": "quantityToInvoice", "value": "5"},
                {"name": "inventory", "value": "WID-A"},
                {"name": "uom", "value": "pcs"},
                {"name": "vatCode", "value": "VAT25"},
                {"name": "vatCodeId", "value": "VAT-001"},
            ]
        }

        data = extract_item_data(item, DocumentKind.PURCHASE_ORDER, 0)

        assert data["number"] == 1
        assert data["description"] == "Widget A"
        assert data["unit-price"] == 10.50
        assert data["quantity"] == 5.0
        assert data["item-id"] == "WID-A"
        assert data["unit-of-measure"] == "pcs"
        assert data["vat-code"] == "VAT25"
        assert data["vat-code-id"] == "VAT-001"
        assert data["item_index"] == 0
        assert data["document_kind"] == DocumentKind.PURCHASE_ORDER
        assert data["raw_item"] == item

    def test_extract_invoice_item(self):
        """Test extracting data from invoice item."""
        item = {
            "fields": [
                {"name": "lineNumber", "value": "2"},
                {"name": "text", "value": "Service B"},
                {"name": "quantity", "value": "3"},
                {"name": "inventory", "value": "SER-B"},
            ],
            "purchaseReceiptDataUnitAmount": "50.00",
            "purchaseReceiptDataQuantity": "3",
        }

        data = extract_item_data(item, DocumentKind.INVOICE, 1)

        assert data["number"] == 2
        assert data["description"] == "Service B"
        assert data["unit-price"] == 50.0
        assert data["unit-price-adjusted"] == 50.0
        assert data["quantity"] == 3.0
        assert data["item-id"] == "SER-B"
        assert data["item_index"] == 1
        assert data["document_kind"] == DocumentKind.INVOICE

    def test_extract_delivery_receipt_item(self):
        """Test extracting data from delivery receipt item."""
        item = {
            "fields": [
                {"name": "lineNumber", "value": "3"},
                {"name": "inventoryDescription", "value": "Product C"},
                {"name": "unitAmount", "value": "25.00"},
                {"name": "quantity", "value": "10"},
                {"name": "inventoryNumber", "value": "PRD-C"},
                {"name": "uom", "value": "kg"},
            ]
        }

        data = extract_item_data(item, DocumentKind.DELIVERY_RECEIPT, 2)

        assert data["number"] == 3
        assert data["description"] == "Product C"
        assert data["unit-price"] == 25.0
        assert data["quantity"] == 10.0
        assert data["item-id"] == "PRD-C"
        assert data["unit-of-measure"] == "kg"
        assert data["item_index"] == 2
        assert data["document_kind"] == DocumentKind.DELIVERY_RECEIPT

    def test_extract_item_with_newlines(self):
        """Test that newlines in descriptions are replaced with spaces."""
        item = {
            "fields": [
                {"name": "text", "value": "Line 1\nLine 2\nLine 3"},
            ]
        }

        data = extract_item_data(item, DocumentKind.INVOICE, 0)

        assert data["description"] == "Line 1 Line 2 Line 3"

    def test_extract_item_invalid_numbers(self):
        """Test handling of invalid number values."""
        item = {
            "fields": [
                {"name": "lineNumber", "value": "not-a-number"},
                {"name": "unitAmount", "value": "invalid"},
                {"name": "quantityToInvoice", "value": "xyz"},
            ]
        }

        data = extract_item_data(item, DocumentKind.PURCHASE_ORDER, 0)

        assert data["number"] is None
        assert data["unit-price"] is None
        assert data["quantity"] is None

    def test_extract_item_none_values(self):
        """Test handling of None values."""
        item = {
            "fields": [
                {"name": "lineNumber", "value": None},
                {"name": "unitAmount", "value": None},
            ]
        }

        data = extract_item_data(item, DocumentKind.PURCHASE_ORDER, 0)

        assert data["number"] is None
        assert data["unit-price"] is None

    def test_extract_item_unknown_document_kind(self, caplog):
        """Test handling of unknown document kind."""
        item = {"fields": [{"name": "test", "value": "test"}]}

        with caplog.at_level(logging.WARNING):
            data = extract_item_data(item, "unknown-type", 0)

        assert data is None
        assert "Unknown document kind" in caplog.text

    def test_extract_invoice_item_fallback_fields(self):
        """Test invoice item extraction with fallback fields."""
        item = {
            "fields": [
                {"name": "lineNumber", "value": "1"},
                {"name": "text", "value": "Item"},
                {"name": "unit-price", "value": "10.00"},
                {"name": "quantity", "value": "2"},
                {"name": "inventory", "value": "ITM-001"},
            ]
        }

        data = extract_item_data(item, DocumentKind.INVOICE, 0)

        # Should use fallback fields when purchaseReceiptData fields are not present
        assert data["unit-price"] == 10.0
        assert data["quantity"] == 2.0
        assert data["item-id"] == "ITM-001"


class TestGetDocumentItems:
    """Test the get_document_items function."""

    def test_get_purchase_order_items(self):
        """Test extracting items from a purchase order."""
        doc = {
            "id": "po-1",
            "headers": [
                {"name": "kind", "value": "purchase-order"}
            ],
            "items": [
                {
                    "fields": [
                        {"name": "lineNumber", "value": "1"},
                        {"name": "description", "value": "Widget A"},
                        {"name": "unitAmount", "value": "10.50"},
                        {"name": "quantityToInvoice", "value": "5"},
                    ]
                },
                {
                    "fields": [
                        {"name": "lineNumber", "value": "2"},
                        {"name": "description", "value": "Widget B"},
                        {"name": "unitAmount", "value": "20.00"},
                        {"name": "quantityToInvoice", "value": "3"},
                    ]
                }
            ]
        }

        items = get_document_items(doc)

        assert len(items) == 2
        assert items[0]["number"] == 1
        assert items[0]["description"] == "Widget A"
        assert items[1]["number"] == 2
        assert items[1]["description"] == "Widget B"

    def test_get_invoice_items(self):
        """Test extracting items from an invoice."""
        doc = {
            "id": "inv-1",
            "headers": [
                {"name": "kind", "value": "invoice"}
            ],
            "items": [
                {
                    "fields": [
                        {"name": "lineNumber", "value": "1"},
                        {"name": "text", "value": "Service A"},
                        {"name": "quantity", "value": "1"},
                    ]
                }
            ]
        }

        items = get_document_items(doc)

        assert len(items) == 1
        assert items[0]["description"] == "Service A"
        assert items[0]["document_kind"] == DocumentKind.INVOICE

    def test_get_delivery_receipt_items(self):
        """Test extracting items from a delivery receipt."""
        doc = {
            "id": "del-1",
            "headers": [
                {"name": "kind", "value": "delivery-receipt"}
            ],
            "items": [
                {
                    "fields": [
                        {"name": "lineNumber", "value": "1"},
                        {"name": "inventoryDescription", "value": "Product A"},
                        {"name": "quantity", "value": "10"},
                    ]
                }
            ]
        }

        items = get_document_items(doc)

        assert len(items) == 1
        assert items[0]["description"] == "Product A"
        assert items[0]["document_kind"] == DocumentKind.DELIVERY_RECEIPT

    def test_invalid_document_format(self, caplog):
        """Test handling of invalid document format (not a dict)."""
        with caplog.at_level(logging.WARNING):
            items = get_document_items("not a dict")

        assert items == []
        assert "Invalid document format" in caplog.text

    def test_missing_document_kind(self, caplog):
        """Test handling of missing document kind."""
        doc = {
            "id": "doc-1",
            "items": []
        }

        with caplog.at_level(logging.WARNING):
            items = get_document_items(doc)

        assert items == []
        assert "Document kind is missing" in caplog.text

    def test_invalid_document_kind(self, caplog):
        """Test handling of invalid document kind value."""
        doc = {
            "id": "doc-1",
            "headers": [
                {"name": "kind", "value": "unknown-type"}
            ],
            "items": []
        }

        with caplog.at_level(logging.WARNING):
            items = get_document_items(doc)

        assert items == []
        assert "Invalid or missing document kind" in caplog.text

    def test_items_not_a_list(self, caplog):
        """Test handling when items field is not a list."""
        doc = {
            "id": "doc-1",
            "headers": [
                {"name": "kind", "value": "invoice"}
            ],
            "items": "not a list"
        }

        with caplog.at_level(logging.WARNING):
            items = get_document_items(doc)

        assert items == []
        assert "items format is not a list" in caplog.text

    def test_items_field_fallback(self):
        """Test fallback to root-level items when not in headers."""
        doc = {
            "id": "doc-1",
            "kind": "invoice",
            "items": [
                {
                    "fields": [
                        {"name": "lineNumber", "value": "1"},
                        {"name": "text", "value": "Item A"},
                    ]
                }
            ]
        }

        items = get_document_items(doc)

        assert len(items) == 1
        assert items[0]["description"] == "Item A"

    def test_skip_non_dict_items(self, caplog):
        """Test that non-dict items are skipped."""
        doc = {
            "id": "doc-1",
            "headers": [
                {"name": "kind", "value": "invoice"}
            ],
            "items": [
                {
                    "fields": [
                        {"name": "lineNumber", "value": "1"},
                        {"name": "text", "value": "Valid Item"},
                    ]
                },
                "invalid item",
                None,
                {
                    "fields": [
                        {"name": "lineNumber", "value": "2"},
                        {"name": "text", "value": "Another Valid Item"},
                    ]
                }
            ]
        }

        with caplog.at_level(logging.WARNING):
            items = get_document_items(doc)

        assert len(items) == 2
        assert items[0]["description"] == "Valid Item"
        assert items[1]["description"] == "Another Valid Item"
        assert caplog.text.count("Skipping non-dict item") == 2

    def test_empty_items_list(self):
        """Test document with empty items list."""
        doc = {
            "id": "doc-1",
            "headers": [
                {"name": "kind", "value": "invoice"}
            ],
            "items": []
        }

        items = get_document_items(doc)

        assert items == []

    def test_missing_items_field(self):
        """Test document with no items field."""
        doc = {
            "id": "doc-1",
            "headers": [
                {"name": "kind", "value": "invoice"}
            ]
        }

        items = get_document_items(doc)

        assert items == []

    def test_items_with_failed_extraction(self, caplog):
        """Test that items with failed extraction are not included."""
        doc = {
            "id": "doc-1",
            "headers": [
                {"name": "kind", "value": "unknown-type"}
            ],
            "items": [
                {"fields": [{"name": "test", "value": "test"}]}
            ]
        }

        with caplog.at_level(logging.WARNING):
            items = get_document_items(doc)

        # Should return empty list since document kind is invalid
        assert items == []
