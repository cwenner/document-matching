# API Sample: Purchase Order input/final

An example of a shared anonymized object and the intended encoding.

## Encoding notes:

- There’s no need to repeat the same organization object multiple times. The top-level organization object can be added to headers and the rest dropped.
- Same for currency.
- Not sure we need all the supplier fields. Some supplier fields are very important however - like id, name, bankgiro, postgiro, vat reg, org number.
- quantityOnInvoices is a very important field and we need all values here, though how this dict of lists is represented is flexible.
- Empty values (null, empty list) can be omitted or made “”.
- The feature lists, if supplied, should probably be treated more as a list of values “FEATURE”: “1”
- Omni does not need all of these fields.

## Encoded

```json
{
  "version": "v3",
  "kind": "purchase-order",
  "site": "falcon-logistics",
  "id": "d7382f41-bc2e-4f27-9b29-12e84f9b0f56",
  "stage": "final",
  "headers": [
    { "name": "creationTime", "value": "2024-08-28T11:14:31.348192Z" },
    { "name": "updateTime", "value": "2024-09-27T21:21:06.097621Z" },
    { "name": "externalId", "value": "000087" },
    { "name": "orderNumber", "value": "000087" },
    { "name": "description", "value": "INV20240828" },

    { "name": "paymentTermsValue", "value": "45" },
    { "name": "paymentTermsType", "value": "DAYS" },

    { "name": "supplierId", "value": "c4956a18-5de1-437b-a6df-72b8123d98b7" },
    { "name": "supplierCreationTime", "value": "2024-03-15T09:21:00.83938Z" },
    { "name": "supplierUpdateTime", "value": "2024-09-15T14:55:10.99372Z" },
    { "name": "supplierNumber", "value": "98231" },
    { "name": "supplierName", "value": "Orion Industrial Ltd" },
    { "name": "supplierExternalId", "value": "65789" },
    { "name": "supplierBankgiro", "value": "348-9021" },
    { "name": "supplierPlusgiro", "value": "2024-09-15 00:00:00" },
    { "name": "supplierVatRegistrationNumber", "value": "SE987654321001" },
    { "name": "supplierOrgNumber", "value": "556789-1234" },
    { "name": "supplierIncomingId", "value": "5567891234" },
    { "name": "supplierActive", "value": "1" },
    { "name": "supplierBlockPayment", "value": "0" },

    { "name": "supplierVatCodeId", "value": "8943a8c2-dcba-4ef6-85e9-9f2c3b0a43f6" },
    { "name": "supplierVatCodeCode", "value": "01" },
    { "name": "supplierVatCodeExternalId", "value": "01" },
    { "name": "supplierVatCodeDescription", "value": "Equipment, 15% VAT" },
    { "name": "supplierVatCodeActive", "value": "1" },
    { "name": "supplierVatCodeOrganizationName", "value": "Falcon Logistics" },

    { "name": "supplierAddressStreet", "value": "Warehouse District 5" },
    { "name": "supplierAddressCity", "value": "Springfield" },
    { "name": "supplierAddressCountry", "value": "USA" },
    { "name": "supplierAddressPostalCode", "value": "34567" },

    { "name": "supplierContactName", "value": "Orion Industrial Ltd" },
    { "name": "supplierContactPhone", "value": "555-423-1987" },
    { "name": "supplierContactEmail", "value": "orders@orionind.com" },
    { "name": "supplierContactExternalId", "value": "90876" },
    { "name": "supplierContactWebsite", "value": "www.orionind.com" },
    { "name": "supplierContactFax", "value": "555-423-1988" },

    { "name": "orderDate", "value": "2024-08-28" },
    { "name": "dueDate", "value": "2024-09-12" },
    { "name": "status", "value": "OPEN" },
    { "name": "exchangeRate", "value": "1.150" },
    { "name": "incVatAmount", "value": "3906.25" },
    { "name": "excVatAmount", "value": "3125.00" },
    { "name": "vatAmount", "value": "781.25" },
    { "name": "quantityOrdered", "value": "14.0" },
    { "name": "quantityToReceive", "value": "0.0" },
    { "name": "quantityReceived", "value": "14.0" },
    { "name": "quantityToInvoice", "value": "14.0" },
    { "name": "quantityInvoiced", "value": "14.0" }
  ],
  "items": [
    {
      "fields": [
        { "name": "id", "value": "87e3b462-47bf-4d8b-988b-2b4d82f6e2a1" },
        { "name": "lineNumber", "value": "1" },
        { "name": "inventoryNumber", "value": "PX-4015-72" },
        { "name": "description", "value": "High-Pressure Hose 1.5m" },
        { "name": "uom", "value": "UNIT" },
        { "name": "orderDate", "value": "2024-08-28" },
        { "name": "dueDate", "value": "2024-09-12" },
        { "name": "amount", "value": "0.00" },
        { "name": "unitAmount", "value": "245.00" },
        { "name": "quantityOrdered", "value": "10.0" },
        { "name": "quantityReceived", "value": "10.0" },
        { "name": "quantityToInvoice", "value": "10.0" },

        { "name": "quantityOnInvoices0-receiptNumber", "value": "000045" },
        { "name": "quantityOnInvoices0-receiptLineNumber", "value": "1" },
        { "name": "quantityOnInvoices0-quantity", "value": "10.0" },

        { "name": "vatCode", "value": "15" },
        { "name": "account", "value": "5632" }
      ]
    },
    {
      "fields": [
        { "name": "id", "value": "c214da7a-3b79-4d6c-8d8d-f612b92ea3bd" },
        { "name": "lineNumber", "value": "2" },
        { "name": "inventoryNumber", "value": "PX-3012-60" },
        { "name": "description", "value": "Adjustable Wrench 12-inch" },
        { "name": "uom", "value": "UNIT" },
        { "name": "orderDate", "value": "2024-08-28" },
        { "name": "dueDate", "value": "2024-09-12" },
        { "name": "amount", "value": "0.00" },
        { "name": "unitAmount", "value": "165.00" },
        { "name": "quantityOrdered", "value": "4.0" },
        { "name": "quantityReceived", "value": "4.0" },
        { "name": "quantityToInvoice", "value": "4.0" },

        { "name": "quantityOnInvoices0-0-receiptNumber", "value": "000045" },
        { "name": "quantityOnInvoices0-0-receiptLineNumber", "value": "3" },
        { "name": "quantityOnInvoices0-0-quantity", "value": "4.0" },
        { "name": "quantityOnInvoices0-1-receiptNumber", "value": "000045" },
        { "name": "quantityOnInvoices0-1-receiptLineNumber", "value": "3" },
        { "name": "quantityOnInvoices0-1-quantity", "value": "4.0" },
        
        { "name": "quantityOnInvoices10-0-receiptNumber", "value": "000046" },
        { "name": "quantityOnInvoices10-0-receiptLineNumber", "value": "4" },
        { "name": "quantityOnInvoices10-0-quantity", "value": "5.0" },
        
        //QuantityOnInvoicesErp TODO, annars kommer kund få förslag på det som redan är klart

        { "name": "vatCode", "value": "15" },
        { "name": "account", "value": "5632" }
      ]
    }
  ]
}

```

## Original

Here show with object repetitions removed (organization, currency).

```jsx
{
  "id": "d7382f41-bc2e-4f27-9b29-12e84f9b0f56",
  "creationTime": "2024-08-28T11:14:31.348192Z",
  "updateTime": "2024-09-27T21:21:06.097621Z",
  "externalId": "000087",
  "orderNumber": "000087",
  "supplierRef": "FAL-00122",
  "description": "INV20240828",
  "note": "",
  "paymentTerms": {
    "value": "45",
    "type": "DAYS"
  },
  "supplier": {
    "id": "c4956a18-5de1-437b-a6df-72b8123d98b7",
    "creationTime": "2024-03-15T09:21:00.83938Z",
    "updateTime": "2024-09-15T14:55:10.99372Z",
    "number": "98231",
    "name": "Orion Industrial Ltd",
    "externalId": "65789",
    "bankgiro": "348-9021",
    "plusgiro": "2024-09-15 00:00:00",
    "vatRegistrationNumber": "SE987654321001",
    "orgNumber": "556789-1234",
    "incomingId": "5567891234",
    "note": "",
    "active": true,
    "blockPayment": false,
    "vatCode": {
      "id": "8943a8c2-dcba-4ef6-85e9-9f2c3b0a43f6",
      "code": "15",
      "externalId": "15",
      "description": "Equipment, 15% VAT",
      "percentage": 15.00,
      "active": true,
      "organizationName": "Falcon Logistics"
    },
    "address": {
      "street": "Warehouse District 5",
      "city": "Springfield",
      "country": "USA",
      "postalCode": "34567"
    },
    "contact": {
      "name": "Orion Industrial Ltd",
      "phone": "555-423-1987",
      "email": "orders@orionind.com",
      "externalId": "90876",
      "website": "www.orionind.com",
      "fax": "555-423-1988"
    },
    "paymentTerms": {
      "value": "45",
      "type": "DAYS"
    },
    "organizationName": "Falcon Logistics"
  },
  "orderDate": "2024-08-28",
  "dueDate": "2024-09-12",
  "status": "OPEN",
  "exchangeRate": 1.150,
  "incVatAmount": 3906.25,
  "excVatAmount": 3125.00,
  "vatAmount": 781.25,
  "quantityOrdered": 14.0,
  "quantityToReceive": 0.0,
  "quantityReceived": 14.0,
  "quantityToInvoice": 14.0,
  "quantityInvoiced": 14.0,
  "lines": [
    {
      "id": "87e3b462-47bf-4d8b-988b-2b4d82f6e2a1",
      "lineNumber": 1,
      "inventoryNumber": "PX-4015-72",
      "description": "High-Pressure Hose 1.5m",
      "uom": "UNIT",
      "orderDate": "2024-08-28",
      "dueDate": "2024-09-12",
      // Computed instead as unitAmount * quantityOrdered
      //"amount": 0.0,
      "unitAmount": 245.0,
      "quantityOrdered": 10.0,
      "quantityReceived": 10.0,
      "quantityToInvoice": 10.0,
      "quantityOnInvoices": {
        "0": [{
          "receiptNumber": "000045",
          "receiptLineNumber": 1,
          "quantity": 10.0
        }]
      },
      "vatCode": "15",
      "account": "5632"
    },
    {
      "id": "c214da7a-3b79-4d6c-8d8d-f612b92ea3bd",
      "lineNumber": 2,
      "inventoryNumber": "PX-3012-60",
      "description": "Adjustable Wrench 12-inch",
      "uom": "UNIT",
      "orderDate": "2024-08-28",
      "dueDate": "2024-09-12",
      "amount": 0.0,
      "unitAmount": 165.0,
      "quantityOrdered": 4.0,
      "quantityReceived": 4.0,
      "quantityToInvoice": 4.0,
      "quantityOnInvoices": {
        "0": [
        {
          "receiptNumber": "000045",
          "receiptLineNumber": 3,
          "quantity": 4.0
        },
        {
          "receiptNumber": "000046",
          "receiptLineNumber": 4,
          "quantity": 5.0
        }
      ],
      "10": [{
          "receiptNumber": "000045",
          "receiptLineNumber": 3,
          "quantity": 4.0
        }]
      },
      "vatCode": "15",
      "account": "5632"
    }
  ]
}
```