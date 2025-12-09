"""
Unit tests for document_utils module.

Tests cover:
- DocumentKind enum values and string conversions
- get_field() function with list inputs
- get_field() function with dict inputs containing headers
- get_field() function with dict inputs containing fields
- get_field() function with simple dict inputs
- Edge cases: missing fields, null values, invalid types
"""

import pytest

from document_utils import DocumentKind, get_field


class TestDocumentKind:
    """Tests for DocumentKind enum."""

    def test_invoice_value(self):
        """Test that INVOICE has correct string value."""
        assert DocumentKind.INVOICE == "invoice"
        assert DocumentKind.INVOICE.value == "invoice"

    def test_purchase_order_value(self):
        """Test that PURCHASE_ORDER has correct string value."""
        assert DocumentKind.PURCHASE_ORDER == "purchase-order"
        assert DocumentKind.PURCHASE_ORDER.value == "purchase-order"

    def test_delivery_receipt_value(self):
        """Test that DELIVERY_RECEIPT has correct string value."""
        assert DocumentKind.DELIVERY_RECEIPT == "delivery-receipt"
        assert DocumentKind.DELIVERY_RECEIPT.value == "delivery-receipt"

    def test_enum_string_comparison(self):
        """Test that enum members can be compared with strings."""
        assert DocumentKind.INVOICE == "invoice"
        assert DocumentKind.PURCHASE_ORDER == "purchase-order"
        assert DocumentKind.DELIVERY_RECEIPT == "delivery-receipt"

    def test_all_enum_members(self):
        """Test that all expected enum members exist."""
        expected_kinds = {"INVOICE", "PURCHASE_ORDER", "DELIVERY_RECEIPT"}
        actual_kinds = {kind.name for kind in DocumentKind}
        assert actual_kinds == expected_kinds


class TestGetFieldWithList:
    """Tests for get_field() with list inputs."""

    def test_list_with_matching_name(self):
        """Test retrieving value from list with matching name."""
        element = [
            {"name": "invoice_number", "value": "INV-12345"},
            {"name": "total", "value": "1000.00"},
        ]
        result = get_field(element, "invoice_number")
        assert result == "INV-12345"

    def test_list_with_multiple_items(self):
        """Test retrieving value from list with multiple items."""
        element = [
            {"name": "field1", "value": "value1"},
            {"name": "field2", "value": "value2"},
            {"name": "field3", "value": "value3"},
        ]
        result = get_field(element, "field2")
        assert result == "value2"

    def test_list_with_no_matching_name(self):
        """Test that None is returned when no name matches."""
        element = [
            {"name": "field1", "value": "value1"},
            {"name": "field2", "value": "value2"},
        ]
        result = get_field(element, "field3")
        assert result is None

    def test_list_with_non_dict_items(self):
        """Test that non-dict items in list are skipped."""
        element = [
            "not-a-dict",
            {"name": "field1", "value": "value1"},
            123,
            {"name": "field2", "value": "value2"},
        ]
        result = get_field(element, "field2")
        assert result == "value2"

    def test_empty_list(self):
        """Test that empty list returns None."""
        result = get_field([], "any_key")
        assert result is None

    def test_list_with_missing_name_key(self):
        """Test list with dicts missing 'name' key."""
        element = [
            {"value": "value1"},
            {"name": "field2", "value": "value2"},
        ]
        result = get_field(element, "field2")
        assert result == "value2"

    def test_list_with_missing_value_key(self):
        """Test list with dicts missing 'value' key."""
        element = [
            {"name": "field1"},
            {"name": "field2", "value": "value2"},
        ]
        result = get_field(element, "field1")
        assert result is None

    def test_list_with_none_value(self):
        """Test that None value is returned correctly."""
        element = [{"name": "field1", "value": None}]
        result = get_field(element, "field1")
        assert result is None

    def test_list_with_numeric_value(self):
        """Test that numeric values are returned correctly."""
        element = [{"name": "quantity", "value": 42}]
        result = get_field(element, "quantity")
        assert result == 42

    def test_list_with_first_match_wins(self):
        """Test that first matching name is returned."""
        element = [
            {"name": "field1", "value": "first"},
            {"name": "field1", "value": "second"},
        ]
        result = get_field(element, "field1")
        assert result == "first"


class TestGetFieldWithDictHeaders:
    """Tests for get_field() with dict inputs containing headers."""

    def test_dict_with_headers_matching_name(self):
        """Test retrieving value from dict with headers."""
        element = {
            "headers": [
                {"name": "date", "value": "2024-01-01"},
                {"name": "vendor", "value": "ACME Corp"},
            ]
        }
        result = get_field(element, "vendor")
        assert result == "ACME Corp"

    def test_dict_with_empty_headers(self):
        """Test dict with empty headers list."""
        element = {"headers": []}
        result = get_field(element, "any_key")
        assert result is None

    def test_dict_with_headers_no_match(self):
        """Test dict with headers but no matching name."""
        element = {
            "headers": [{"name": "field1", "value": "value1"}]
        }
        result = get_field(element, "field2")
        assert result is None

    def test_dict_with_headers_and_fields_prefers_headers(self):
        """Test that headers are checked before fields."""
        element = {
            "headers": [{"name": "key1", "value": "from_headers"}],
            "fields": [{"name": "key1", "value": "from_fields"}]
        }
        result = get_field(element, "key1")
        assert result == "from_headers"

    def test_dict_with_headers_non_dict_items(self):
        """Test dict with non-dict items in headers."""
        element = {
            "headers": [
                "not-a-dict",
                {"name": "field1", "value": "value1"},
            ]
        }
        result = get_field(element, "field1")
        assert result == "value1"


class TestGetFieldWithDictFields:
    """Tests for get_field() with dict inputs containing fields."""

    def test_dict_with_fields_matching_name(self):
        """Test retrieving value from dict with fields."""
        element = {
            "fields": [
                {"name": "description", "value": "Steel bolt"},
                {"name": "quantity", "value": "100"},
            ]
        }
        result = get_field(element, "description")
        assert result == "Steel bolt"

    def test_dict_with_empty_fields(self):
        """Test dict with empty fields list."""
        element = {"fields": []}
        result = get_field(element, "any_key")
        assert result is None

    def test_dict_with_fields_no_match(self):
        """Test dict with fields but no matching name."""
        element = {
            "fields": [{"name": "field1", "value": "value1"}]
        }
        result = get_field(element, "field2")
        assert result is None

    def test_dict_with_fields_non_dict_items(self):
        """Test dict with non-dict items in fields."""
        element = {
            "fields": [
                123,
                {"name": "field1", "value": "value1"},
            ]
        }
        result = get_field(element, "field1")
        assert result == "value1"

    def test_dict_with_both_headers_and_fields(self):
        """Test dict with both headers and fields checks both."""
        element = {
            "headers": [{"name": "header_key", "value": "header_value"}],
            "fields": [{"name": "field_key", "value": "field_value"}]
        }
        assert get_field(element, "header_key") == "header_value"
        assert get_field(element, "field_key") == "field_value"

    def test_dict_with_headers_fallback_to_fields(self):
        """Test that fields are checked when header doesn't match."""
        element = {
            "headers": [{"name": "header_key", "value": "header_value"}],
            "fields": [{"name": "field_key", "value": "field_value"}]
        }
        result = get_field(element, "field_key")
        assert result == "field_value"


class TestGetFieldWithSimpleDict:
    """Tests for get_field() with simple dict inputs."""

    def test_simple_dict_with_matching_key(self):
        """Test retrieving value from simple dict."""
        element = {"invoice_number": "INV-12345", "total": "1000.00"}
        result = get_field(element, "invoice_number")
        assert result == "INV-12345"

    def test_simple_dict_with_no_matching_key(self):
        """Test that None is returned when key doesn't exist."""
        element = {"field1": "value1"}
        result = get_field(element, "field2")
        assert result is None

    def test_empty_dict(self):
        """Test that empty dict returns None."""
        result = get_field({}, "any_key")
        assert result is None

    def test_dict_with_none_value(self):
        """Test that None value is returned correctly."""
        element = {"field1": None}
        result = get_field(element, "field1")
        assert result is None

    def test_dict_with_numeric_value(self):
        """Test that numeric values are returned correctly."""
        element = {"count": 42, "price": 99.99}
        assert get_field(element, "count") == 42
        assert get_field(element, "price") == 99.99

    def test_dict_with_nested_dict_value(self):
        """Test that nested dict values are returned correctly."""
        nested = {"nested_key": "nested_value"}
        element = {"field1": nested}
        result = get_field(element, "field1")
        assert result == nested

    def test_dict_with_list_value(self):
        """Test that list values are returned correctly."""
        list_value = [1, 2, 3]
        element = {"field1": list_value}
        result = get_field(element, "field1")
        assert result == list_value

    def test_dict_headers_fields_fallback_to_direct_key(self):
        """Test fallback to direct key access when headers/fields don't match."""
        element = {
            "headers": [{"name": "header_key", "value": "header_value"}],
            "fields": [{"name": "field_key", "value": "field_value"}],
            "direct_key": "direct_value"
        }
        result = get_field(element, "direct_key")
        assert result == "direct_value"

    def test_dict_with_no_headers_or_fields(self):
        """Test dict without headers or fields uses direct key access."""
        element = {"key1": "value1", "key2": "value2"}
        assert get_field(element, "key1") == "value1"
        assert get_field(element, "key2") == "value2"


class TestGetFieldEdgeCases:
    """Tests for get_field() edge cases and error handling."""

    def test_invalid_element_type_string_raises_exception(self):
        """Test that string input raises exception."""
        with pytest.raises(Exception) as exc_info:
            get_field("not-a-dict-or-list", "key")
        assert "Invalid element type" in str(exc_info.value)
        assert "Expected dict or list" in str(exc_info.value)

    def test_invalid_element_type_int_raises_exception(self):
        """Test that int input raises exception."""
        with pytest.raises(Exception) as exc_info:
            get_field(123, "key")
        assert "Invalid element type" in str(exc_info.value)

    def test_invalid_element_type_none_raises_exception(self):
        """Test that None input raises exception."""
        with pytest.raises(Exception) as exc_info:
            get_field(None, "key")
        assert "Invalid element type" in str(exc_info.value)

    def test_invalid_element_type_tuple_raises_exception(self):
        """Test that tuple input raises exception."""
        with pytest.raises(Exception) as exc_info:
            get_field((1, 2, 3), "key")
        assert "Invalid element type" in str(exc_info.value)

    def test_invalid_element_type_set_raises_exception(self):
        """Test that set input raises exception."""
        with pytest.raises(Exception) as exc_info:
            get_field({1, 2, 3}, "key")
        assert "Invalid element type" in str(exc_info.value)

    def test_list_with_all_non_dict_items(self):
        """Test list with no dict items returns None."""
        element = ["string", 123, True, None]
        result = get_field(element, "any_key")
        assert result is None

    def test_dict_with_headers_not_list(self):
        """Test dict where headers is not a list."""
        element = {"headers": "not-a-list"}
        result = get_field(element, "any_key")
        assert result is None

    def test_dict_with_fields_not_list(self):
        """Test dict where fields is not a list."""
        element = {"fields": "not-a-list"}
        result = get_field(element, "any_key")
        assert result is None

    def test_case_sensitive_key_matching(self):
        """Test that key matching is case-sensitive."""
        element = [{"name": "Field1", "value": "value1"}]
        assert get_field(element, "Field1") == "value1"
        assert get_field(element, "field1") is None
        assert get_field(element, "FIELD1") is None

    def test_empty_string_key(self):
        """Test searching for empty string key."""
        element = [{"name": "", "value": "empty_key_value"}]
        result = get_field(element, "")
        assert result == "empty_key_value"

    def test_special_characters_in_key(self):
        """Test keys with special characters."""
        element = [
            {"name": "key-with-dashes", "value": "value1"},
            {"name": "key.with.dots", "value": "value2"},
            {"name": "key_with_underscores", "value": "value3"},
        ]
        assert get_field(element, "key-with-dashes") == "value1"
        assert get_field(element, "key.with.dots") == "value2"
        assert get_field(element, "key_with_underscores") == "value3"

    def test_unicode_in_values(self):
        """Test that unicode values are handled correctly."""
        element = [{"name": "field1", "value": "Hello \u4e16\u754c"}]
        result = get_field(element, "field1")
        assert result == "Hello \u4e16\u754c"

    def test_boolean_values(self):
        """Test that boolean values are returned correctly."""
        element = [
            {"name": "is_active", "value": True},
            {"name": "is_deleted", "value": False},
        ]
        assert get_field(element, "is_active") is True
        assert get_field(element, "is_deleted") is False

    def test_zero_value(self):
        """Test that zero value is returned correctly (not treated as None)."""
        element = [{"name": "count", "value": 0}]
        result = get_field(element, "count")
        assert result == 0

    def test_empty_string_value(self):
        """Test that empty string value is returned correctly."""
        element = [{"name": "field1", "value": ""}]
        result = get_field(element, "field1")
        assert result == ""
