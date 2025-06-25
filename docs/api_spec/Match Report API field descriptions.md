# Match Report API field descriptions

## Fields

### Top-level fields

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| version | string enum | Always `v3`. |
| id | string | Globally unique and ascending identifier set for the match report. |
| kind | string enum | Always `match-report`. |
| site | string | Repeat of the `site` provided for the triggering input. |
| stage | string enum | Always `output` when supplied by us; `final` if corrected and returned by the platform. |
| headers | array | Reserved for metadata but presently an empty list. |
| documents | array[DocumentRef] | Described in section below. |
| labels | array[string] | Described in section below. |
| metrics | array | Described in section below. |
| deviations | array[Deviation] | Described in section below. |
| itempairs | array[Itempair] | Described in section below. |

### Documents

Identifiers specifying which documents have been used to produce match reports.

**Is a list of:**

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| kind | string enum | enum: `invoice` | `purchase-order` | `delivery-receipt` |
| id | string | id of the document, as provided when sent to the API. |

**Notes:**

- Presently for three-way matching, two different match reports are produced: One between Invoice and Purchase Order; and between Purchase Order and Delivery Receipt.

### Labels

Free-form list of strings signaling cases of interest. Have to be a kebab-case.

Omnimodular currently provides these labels: `no-match`, `matched`.

Customers could e.g. provide labels such as `not-shown` if a report was never used in the UI, or `rejected` if it was shown but discarded.

### Metrics

**Is a list of *name-value pairs* of:**

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| certainty | number | Predicted probability that the matching is correct - i.e. these documents will be paired in the system with the rows paired as stated. |
| deviation-severity | string enum | One of: `no-severity`, `info`, `low`, `medium`, `high`. Refers to the overall severity of deviations in the match. |
| invoice-has-future-match-certainty | optional number | Predicted probability that the invoice in the match (if any), will get a future document to be matched against. This can be used to decide whether to hold or process the document. Special case is that an invoice can be marked as done even though the second match report is between the PO and delivery receipt. |
| purchase-order-has-future-match-certainty | optional number | Predicted probability that the purchase order in the report (if any), will get a future document to be matched against. |
| delivery-receipt-has-future-match-certainty | optional number | Predicted probability that the delivery receipt in the report (if any), will get a future document to be matched against. |

### Deviations

**Is a list of:**

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| code | string enum | The kind of deviation that has been detected. See section below for deviation codes. |
| severity | string enum | One of: `no-severity`, `info`, `low`, `medium`, `high`. |
| message | string | Human-readable description of the deviation. Suitable for developers, not end users. |
| field_names | array[string] | Attempts to reference which fields in the respective documents caused the deviation. This is a list with one element per document in `documents`. E.g. when a deviation is detected in amounts between two documents, the amount fields may have different names in the two documents. |
| values | array[any as string] | For the above-mentioned field names, what were the values in the documents. Encoded as strings. |

### Itempairs

List of items that have been paired. Despite the name, this does not mean that there is a pair of items - it can be also be individual items that could not be paired.

**Is a list of:**

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| fields | array | See below. |

**fields is a list of:**

| **Field** | **Type** | **Description** |
| --- | --- | --- |
| match_type | string enum | Clarifies the type of match of the pairing. Currently `matched` or `unmatched`. |
| item_indices | array[optional number] | The indices (starting with 0) of the items that have been paired together. This can be an index from each document, i.e. `doc0.items[item_indices[0]]` paired with `doc1.items[item_indices[1]]`. Some of these elements can be `null` if no item in that document was paired, i.e. for an extra unpaired item it could read `[null, 3]` |
| deviation_severity | string enum | One of: `no-severity`, `info`, `low`, `medium`, `high`. |
| item_unchanged_certainty | float | Predicted probability that this pairing of items will be the same when finalized, i.e. matched items will be matched as described, and unmatched remain unmatched. |
| deviations | array[Deviation] | See separate section. |

### Deviation codes

| **Code** | **Header or item** | **Description** |
| --- | --- | --- |
| ITEM_UNMATCHED | Item | Item was expected to match but could not be matched. |
| CURRENCIES_DIFFER | Header | Different currencies in the document headers. |
| AMOUNTS_DIFFER | Header and Item | As described. How much they differ affect severity. |
| PRICES_PER_UNIT_DIFFER | Item | As described. How much they differ affect severity. |
| PARTIAL_DELIVERY | Item | Partial delivery of PO - will be marked as INFO. |
| QUANTITIES_DIFFER | Item | Quantities differ but not a PO partial delivery. |
| DESCRIPTIONS_DIFFER | Item | As described. How much they differ affect severity. |
| ARTICLE_NUMBERS_DIFFER | Item | As described. |
| ITEMS_DIFFER | Item | Prediction based on article numbers, descriptions, or numbers that despite the line items making sense as a match, the items in the two documents are in fact different. |

## Example document with match:

```jsx
{
  "version": "v3",
  "id": "r654",
  "kind": "match-report",
  "site": "falcon-logistics",
  "stage": "output",
  "headers": [],

  "documents": [
    { "kind": "purchase-order", "id": "e7c5a9d2-4b81-49f3-97d6-2a3b8f72c318" },
    { "kind": "invoice", "id": "b5a3c7d2-8f91-4e2a-9d78-6a3b4f92d318" }
  ],

  "labels": [
    "match"
  ],

  "metrics": [
    {"name": "certainty", "value": 0.93151},
    {"name": "deviation-severity", "value": "high"},
    {"name": "invoice-has-future-match-certainty", "value": 0.98},
    {"name": "purchase-order-has-future-match-certainty", "value": 0.99},
    {"name": "delivery-receipt-has-future-match-certainty", "value": null}
  ],

  "deviations": [
    {
      "code": "amounts-differ",
      "severity": "high",
      "message": "Incl VAT amount differs by 42.75",
      "field_names": ["headers.incVatAmount", "headers.inc_vat_amount"],
      "values": ["1950.25", "1993.00"]
    }
  ],

  "itempairs": [
    {
      "item_indices": [2, 3],
      "match_type": "matched",
      "deviation_severity": "medium",
      "item_unchanged_certainty": 0.88,
      "deviations": [
        {
          "field_names": ["fields.quantityToInvoice", "fields.quantity"],
          "values": [9, 11],
          "severity": "medium",
          "message": "Quantity differs by 2",
          "code": "quantity-too-many"
        }
      ]
    }
  ]
}
```