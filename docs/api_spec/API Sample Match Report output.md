# API Sample: Match Report output

Two examples of output objects.

## Document with no match

```jsx
{
  "version": "v3",
  "id": "r987",
  "kind": "match-report",
  "site": "falcon-logistics",
  "stage": "output",
  "headers": [],

  "documents": [
    {
      "kind": "invoice",
      "id": "b5a3c7d2-8f91-4e2a-9d78-6a3b4f92d318"
    }
  ],

  "labels": [
    "no-match"
  ],

  "metrics": [
    {"name": "certainty", "value": 0.95733},
    {"name": "deviation-severity", "value": "no-severity"},
    {"name": "invoice-has-future-match-certainty", "value": 0.88}
  ],

  "deviations": [],
  "itempairs": []
}

```

## Document with match

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
    {"name": "purchase-order-has-future-match-certainty", "value": 0.99}
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