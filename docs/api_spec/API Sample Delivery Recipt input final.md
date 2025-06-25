# API Sample: Delivery Recipt input/final

An example of a shared anonymized object and the intended encoding.

## Encoding notes:

- An id must be supplied. This can be the delivery-receipt number or something else.
- We do not need all of these fields.

## Encoded

Note: This is just an example. The flattening of objects can be done arbitrarily. E.g. one could use names like “supplier_name”, “supplierName”, “supplier.name”.

```jsx

{
  "version": "v3",
  "kind": "delivery-receipt",
  "site": "falcon-logistics",
  "id": "00045",
  "stage": "final",
  "headers": [
    {"name": "receiptType", "value": "PoReceipt"},
    {"name": "receiptNbr", "value": "00045"},
    {"name": "hold", "value": "0"},
    {"name": "status", "value": "Released"},
    {"name": "date", "value": "2024-08-30T00:00:00"},
    {"name": "postPeriod", "value": "202504"},
    {"name": "supplierInternalId", "value": "65789"},
    {"name": "supplierNumber", "value": "98231"},
    {"name": "supplierName", "value": "Orion Industrial Ltd"},
    {"name": "locationId", "value": "Central"},
    {"name": "locationName", "value": "Main Warehouse"},
    {"name": "currency", "value": "USD"},
    {"name": "exchangeRate", "value": "1.150"},
    {"name": "createBill", "value": "0"},
    {"name": "totalQty", "value": "14.0"},
    {"name": "controlQty", "value": "14.0"},
    {"name": "vatExemptTotal", "value": "0.00"},
    {"name": "vatTaxableTotal", "value": "3125.00"},
    {"name": "totalAmt", "value": "3906.25"},
    {"name": "controlTotal", "value": "3906.25"},
    {"name": "lastModifiedDateTime", "value": "2024-09-04T11:18:26.403"},
    {"name": "branchNumberNumber", "value": "1"},
    {"name": "branchNumberName", "value": "Falcon Logistics"},
    {"name": "metadataTotalCount", "value": "812"},
    {"name": "metadataMaxPageSize", "value": "1000"},
    {"name": "supplierRef", "value": "876543"}
  ],
  "items": [
    {
      "fields": [
        {"name": "allocations-0lineNbr", "value": "2"},
        {"name": "allocations-0itemId", "value": "PX-4015-72          "},
        {"name": "allocations-0locationId", "value": "1"},
        {"name": "allocations-0locationName", "value": "Standard"},
        {"name": "allocations-0quantity", "value": "10.0"},
        {"name": "allocations-0uom", "value": "UNIT"},
        {"name": "allocations-0description", "value": "High-Pressure Hose 1.5m"},
        {"name": "lineNbr", "value": "1"},
        {"name": "branchNumberNumber", "value": "1"},
        {"name": "branchNumberName", "value": "Falcon Logistics"},
        {"name": "inventoryNumber", "value": "PX-4015-72"},
        {"name": "inventoryDescription", "value": "High-Pressure Hose 1.5m"},
        {"name": "lineType", "value": "GoodsForInventory"},
        {"name": "warehouseId", "value": "1         "},
        {"name": "warehouseDescription", "value": "Main Storage"},
        {"name": "locationId", "value": "1"},
        {"name": "locationName", "value": "Standard"},
        {"name": "transactionDescription", "value": "High-Pressure Hose 1.5m"},
        {"name": "uom", "value": "UNIT"},
        {"name": "orderQty", "value": "10.0"},
        {"name": "openQty", "value": "0.0"},
        {"name": "receiptQty", "value": "10.0"},
        {"name": "unitCost", "value": "245.00"},
        {"name": "extCost", "value": "2450.00"},
        {"name": "discountPercent", "value": "0.0"},
        {"name": "discountAmount", "value": "0.00"},
        {"name": "manualDiscount", "value": "1"},
        {"name": "amount", "value": "2450.00"},
        {"name": "taxCategoryNumber", "value": "01"},
        {"name": "taxCategoryDescription", "value": "Equipment, 15% VAT"},
        {"name": "actualAccountType", "value": "L"},
        {"name": "actualAccountNumber", "value": "5632"},
        {"name": "actualAccountDescription", "value": "Accrued Supplier Liabilities"},
        {"name": "actualSubId", "value": "000000000000"},
        {"name": "actualSubDescription", "value": "None"},
        {"name": "projectId", "value": "X"},
        {"name": "projectDescription", "value": "Non-Project Code."},
        {"name": "expirationDate", "value": "0001-01-01T00:00:00"},
        {"name": "poOrderType", "value": "RegularOrder"},
        {"name": "poOrderNbr", "value": "000087"},
        {"name": "poOrderLineNbr", "value": "1"}
      ]
    },
    {
      "fields": [
        {"name": "allocations-0LineNbr", "value": "4"},
        {"name": "allocations-0ItemId", "value": "PX-3012-60          "},
        {"name": "allocations-0LocationId", "value": "1"},
        {"name": "allocations-0LocationName", "value": "Standard"},
        {"name": "allocations-0quantity", "value": "4.0"},
        {"name": "allocations-0uom", "value": "UNIT"},
        {"name": "allocations-0description", "value": "Adjustable Wrench 12-inch"},
        {"name": "lineNbr", "value": "3"},
        {"name": "branchNumberNumber", "value": "1"},
        {"name": "branchNumberName", "value": "Falcon Logistics"},
        {"name": "inventoryNumber", "value": "PX-3012-60"},
        {"name": "inventoryDescription", "value": "Adjustable Wrench 12-inch"},
        {"name": "lineType", "value": "GoodsForInventory"},
        {"name": "warehouseId", "value": "1         "},
        {"name": "warehouseDescription", "value": "Main Storage"},
        {"name": "locationId", "value": "1"},
        {"name": "locationName", "value": "Standard"},
        {"name": "transactionDescription", "value": "Adjustable Wrench 12-inch"},
        {"name": "uom", "value": "UNIT"},
        {"name": "orderQty", "value": "4.0"},
        {"name": "openQty", "value": "0.0"},
        {"name": "receiptQty", "value": "4.0"},
        {"name": "unitCost", "value": "165.00"},
        {"name": "extCost", "value": "660.00"},
        {"name": "discountPercent", "value": "0.0"},
        {"name": "discountAmount", "value": "0.00"},
        {"name": "manualDiscount", "value": "1"},
        {"name": "amount", "value": "660.00"},
        {"name": "taxCategoryNumber", "value": "01"},
        {"name": "taxCategoryDescription", "value": "Equipment, 15% VAT"},
        {"name": "actualAccountType", "value": "L"},
        {"name": "actualAccountNumber", "value": "5632"},
        {"name": "actualAccountDescription", "value": "Accrued Supplier Liabilities"},
        {"name": "actualSubId", "value": "000000000000"},
        {"name": "actualSubDescription", "value": "None"},
        {"name": "projectId", "value": "X"},
        {"name": "projectDescription", "value": "Non-Project Code."},
        {"name": "expirationDate", "value": "0001-01-01T00:00:00"},
        {"name": "poOrderType", "value": "RegularOrder"},
        {"name": "poOrderNbr", "value": "000087"},
        {"name": "poOrderLineNbr", "value": "2"}
      ]
    }
  ]
}
```

## Original

```jsx
{
  "landedCost": [],
  "receiptType": "PoReceipt",
  "receiptNbr": "000045",
  "hold": false,
  "status": "Released",
  "date": "2024-08-30T00:00:00",
  "postPeriod": "202504",
  "supplier": {
    "internalId": 65789,
    "number": "98231",
    "name": "Orion Industrial Ltd"
  },
  "location": {
    "id": "Central",
    "name": "Main Warehouse"
  },
  "currency": "USD",
  "exchangeRate": 1.150,
  "createBill": false,
  "totalQty": 14.0,
  "controlQty": 14.0,
  "vatExemptTotal": 0.0,
  "vatTaxableTotal": 3125.0,
  "totalAmt": 3906.25,
  "controlTotal": 3906.25,
  "lastModifiedDateTime": "2024-09-04T11:18:26.403",
  "branchNumber": {
    "number": "1",
    "name": "Falcon Logistics"
  },
  "lines": [
    {
      "allocations": [
        {
          "lineNbr": 2,
          "itemId": "PX-4015-72          ",
          "location": {
            "id": "1",
            "name": "Standard"
          },
          "lotSerialNumber": "",
          "quantity": 10.0,
          "uom": "UNIT",
          "description": "High-Pressure Hose 1.5m"
        }
      ],
      "lineNbr": 1,
      "branchNumber": {
        "number": "1",
        "name": "Falcon Logistics"
      },
      "inventory": {
        "number": "PX-4015-72",
        "description": "High-Pressure Hose 1.5m"
      },
      "lineType": "GoodsForInventory",
      "warehouse": {
        "id": "1         ",
        "description": "Main Storage"
      },
      "location": {
        "id": "1",
        "name": "Standard"
      },
      "transactionDescription": "High-Pressure Hose 1.5m",
      "uom": "UNIT",
      "orderQty": 10.0,
      "openQty": 0.0,
      "receiptQty": 10.0,
      "unitCost": 245.0,
      "extCost": 2450.0,
      "discountPercent": 0.0,
      "discountAmount": 0.0,
      "manualDiscount": true,
      "discountCode": {},
      "amount": 2450.0,
      "taxCategory": {
        "number": "01",
        "description": "Equipment, 15% VAT"
      },
      "actualAccount": {
        "type": "L",
        "number": "5632",
        "description": "Accrued Supplier Liabilities"
      },
      "actualSub": {
        "id": "000000000000",
        "description": "None"
      },
      "project": {
        "id": "X",
        "description": "Non-Project Code."
      },
      "expirationDate": "0001-01-01T00:00:00",
      "lotSerialNumber": "",
      "poOrderType": "RegularOrder",
      "poOrderNbr": "000087",
      "poOrderLineNbr": 1
    },
    {
      "allocations": [
        {
          "lineNbr": 4,
          "itemId": "PX-3012-60          ",
          "location": {
            "id": "1",
            "name": "Standard"
          },
          "lotSerialNumber": "",
          "quantity": 4.0,
          "uom": "UNIT",
          "description": "Adjustable Wrench 12-inch"
        }
      ],
      "lineNbr": 3,
      "branchNumber": {
        "number": "1",
        "name": "Falcon Logistics"
      },
      "inventory": {
        "number": "PX-3012-60",
        "description": "Adjustable Wrench 12-inch"
      },
      "lineType": "GoodsForInventory",
      "warehouse": {
        "id": "1         ",
        "description": "Main Storage"
      },
      "location": {
        "id": "1",
        "name": "Standard"
      },
      "transactionDescription": "Adjustable Wrench 12-inch",
      "uom": "UNIT",
      "orderQty": 4.0,
      "openQty": 0.0,
      "receiptQty": 4.0,
      "unitCost": 165.0,
      "extCost": 660.0,
      "discountPercent": 0.0,
      "discountAmount": 0.0,
      "manualDiscount": true,
      "discountCode": {},
      "amount": 660.0,
      "taxCategory": {
        "number": "01",
        "description": "Equipment, 15% VAT"
      },
      "actualAccount": {
        "type": "L",
        "number": "5632",
        "description": "Accrued Supplier Liabilities"
      },
      "actualSub": {
        "id": "000000000000",
        "description": "None"
      },
      "project": {
        "id": "X",
        "description": "Non-Project Code."
      },
      "expirationDate": "0001-01-01T00:00:00",
      "lotSerialNumber": "",
      "poOrderType": "RegularOrder",
      "poOrderNbr": "000087",
      "poOrderLineNbr": 2
    }
  ],
  "metadata": {
    "totalCount": 812,
    "maxPageSize": 1000
  },
  "supplierRef": "876543"
}
```