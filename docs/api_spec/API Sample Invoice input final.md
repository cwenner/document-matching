# API Sample: Invoice input/final

An example of a shared anonymized object and the intended encoding.

## Encoding notes:

- We would like parts of all of the relevant objects for an invoice: the invoice object, OriginalData, the XML in the original data, the invoice lines (initial lines for input, fakturarader when done).
- The interpreted_xml should be stored as a base64-encoded XML or JSON attachment.
- The interpreted_data could also either be provided as header information or as a base-64-encoded JSON attachment.
- ~~Uncertain: Should quick data be exposed or is this considered likely to change?~~

## Encoded

```json
{
  "version": "v3",
  "kind": "invoice",
  "site": "falcon-logistics",
  "id": "5c21d8a3-b987-4a25-b0f3-4d92e7b6a512",
  "stage": "input",
  "headers": [
    { "name": "creationTime", "value": "2024-08-28 05:06:59.541257" },
    { "name": "updateTime", "value": "2024-10-01 14:56:50.771475" },
    { "name": "blocked", "value": "0" },
    { "name": "bookingDate", "value": "2024-08-27" },
    { "name": "buyerReference", "value": "9000001234" },
    { "name": "dueDate", "value": "2024-09-26" },
    { "name": "erpBookingDate", "value": "2024-08-27" },
    { "name": "erpInvoiceNumber", "value": "INV-567891" },
    { "name": "excVatAmount", "value": "3125.00" },
    { "name": "exchangeRate", "value": "1.150" },
    { "name": "incVatAmount", "value": "3906.25" },
    { "name": "incomingId", "value": "ae29db47-5d38-4c78-83b6-f9e2b7c1d657" },
    { "name": "internalInvoiceNumber", "value": "2345" },
    { "name": "invoiceDate", "value": "2024-08-27" },
    { "name": "invoiceNumber", "value": "FAL-INV-20240827" },
    { "name": "ocr", "value": "FAL-INV-20240827" },
    { "name": "orderReference", "value": "FAL-20240828 - 000087" },
    { "name": "paidDate", "value": "2024-10-01" },
    { "name": "salesOrderReference", "value": "ORD789654" },
    { "name": "status", "value": "PAID" },
    { "name": "type", "value": "DEBIT" },
    { "name": "vatAmount", "value": "781.25" },
    { "name": "version", "value": "12" },
    { "name": "voucher", "value": "INV-567891" },

    { "name": "organizationId", "value": "c21d38e4-7845-4b12-9c3b-5f8a2719e041" },
    { "name": "currencyId", "value": "8f675d3a-4b8e-44e2-a92a-1f3d8b4c92e7" },
    { "name": "supplierId", "value": "a95b4c18-56f1-4d5e-a9df-83b7d123e48b" },
    { "name": "supplierDebtLineId", "value": "9d8a42b1-5d72-4c1a-b9c4-78e3b9d5f6a2" },
    { "name": "vatLineId", "value": "6f472c8d-2b5d-4e78-92f4-31a8d7c5b942" },

    { "name": "approverId", "value": "4b3d92a7-5d8a-4c5e-87b1-2f6a3d8b9c42" },
    { "name": "approverType", "value": "USER_GROUP" },

    { "name": "appliedWorkflows-0", "value": "8d2b5c4a-3f78-4e92-b1d7-6a9c5b8d7f31" },
    { "name": "appliedWorkflows-1", "value": "c5b4729d-2b78-4d8a-92f1-3d6a5b7c9f42" },

    { "name": "periodId", "value": "b21d5a8c-92f4-4e78-93b1-6d3a5c8b7d42" },

    { "name": "autoApproved", "value": "0" },
    { "name": "bankgiro", "value": "9876543" },

    { "name": "creationDetailsSource", "value": "PEPPOLBIS30" },
    { "name": "creationDetailsCreationType", "value": "AUTO_INVOICE" },
    { "name": "creationDetailsCreationFormat", "value": "E_INVOICE" },
    { "name": "creationDetailsReceivingAddress", "value": "0007:5567891234" }
  ],
  "items": [
    {
      "fields": [
        { "name": "id", "value": "98d2b5c4-a7f1-4e92-b1d7-6a9c5b7d8f31" },
        { "name": "creationTime", "value": "2024-08-28 05:06:59.544851" },
        { "name": "updateTime", "value": "2024-08-28 13:14:20.712003" },
        { "name": "debit", "value": "3125.00" },
        { "name": "status", "value": "APPROVED" },
        { "name": "text", "value": "High-Pressure Hose 1.5m" },
        { "name": "accountId", "value": "c5b4729d-2b78-4d8a-92f1-3d6a5b7c9f42" },
        { "name": "invoiceId", "value": "5c21d8a3-b987-4a25-b0f3-4d92e7b6a512" },
        { "name": "vatCodeId", "value": "a21d5c8b-92f4-4e78-93b1-6d3a5c8b7d42" },
        { "name": "approverId", "value": "4b3d92a7-5d8a-4c5e-87b1-2f6a3d8b9c42" },
        { "name": "approverType", "value": "USER_GROUP" },
        { "name": "lineNumber", "value": "1" },
        { "name": "purchaseReceiptDataQuantity", "value": "10.0" },
        { "name": "purchaseReceiptDataLineNumber", "value": "1" },
        { "name": "purchaseReceiptDataUnitAmount", "value": "245.00" },
        { "name": "purchaseReceiptDataOrderNumber", "value": "000087" },
        { "name": "purchaseReceiptDataReceiptNumber", "value": "000045" },
        { "name": "purchaseReceiptDataInventoryNumber", "value": "PX-4015-72" }
      ]
    }
  ],
  "attachments": [
    {
      "name": "interpreted_xml.json",
      "value": "<base64 encoded JSON data>"
    }
  ]
}
```

## Original - Invoice

```jsx
{
  "id": "5c21d8a3-b987-4a25-b0f3-4d92e7b6a512",
  "creation_time": "2024-08-28 05:06:59.541257",
  "update_time": "2024-10-01 14:56:50.771475",
  "blocked": 0,
  "booking_date": "2024-08-27",
  "buyer_reference": "9000001234",
  "due_date": "2024-09-26",
  "erp_booking_date": "2024-08-27",
  "erp_invoice_number": "INV-567891",
  "exc_vat_amount": 3125.00,
  "exchange_rate": 1.150,
  "inc_vat_amount": 3906.25,
  "incoming_id": "ae29db47-5d38-4c78-83b6-f9e2b7c1d657",
  "internal_invoice_number": 2345,
  "invoice_date": "2024-08-27",
  "invoice_number": "FAL-INV-20240827",
  "ocr": "FAL-INV-20240827",
  "order_reference": "FAL-20240828 - 000087",
  "paid_date": "2024-10-01",
  "sales_order_reference": "ORD789654",
  "status": "PAID",
  "type": "DEBIT",
  "vat_amount": 781.25,
  "version": 12,
  "voucher": "INV-567891",
  "organization_id": "c21d38e4-7845-4b12-9c3b-5f8a2719e041",
  "currency_id": "8f675d3a-4b8e-44e2-a92a-1f3d8b4c92e7",
  "supplier_id": "a95b4c18-56f1-4d5e-a9df-83b7d123e48b",
  "supplier_debt_line_id": "9d8a42b1-5d72-4c1a-b9c4-78e3b9d5f6a2",
  "vat_line_id": "6f472c8d-2b5d-4e78-92f4-31a8d7c5b942",
  "approver": {
    "id": "4b3d92a7-5d8a-4c5e-87b1-2f6a3d8b9c42",
    "type": "USER_GROUP"
  },
  "applied_workflows": [
    "8d2b5c4a-3f78-4e92-b1d7-6a9c5b7d8f31",
    "c5b4729d-2b78-4d8a-92f1-3d6a5b7c9f42"
  ],
  "period_id": "b21d5a8c-92f4-4e78-93b1-6d3a5c8b7d42",
  "auto_approved": 0,
  "bankgiro": "9876543",
  "creation_details": {
    "source": "PEPPOLBIS30",
    "creationType": "AUTO_INVOICE",
    "creationFormat": "E_INVOICE",
    "receivingAddress": "0007:5567891234"
  },
  "lines": [
    {
      "id": "98d2b5c4-a7f1-4e92-b1d7-6a9c5b7d8f31",
      "creation_time": "2024-08-28 05:06:59.544851",
      "update_time": "2024-08-28 13:14:20.712003",
      "debit": 3125.00,
      "status": "APPROVED",
      "text": "High-Pressure Hose 1.5m",
      "account_id": "c5b4729d-2b78-4d8a-92f1-3d6a5b7c9f42",
      "invoice_id": "5c21d8a3-b987-4a25-b0f3-4d92e7b6a512",
      "vat_code_id": "a21d5c8b-92f4-4e78-93b1-6d3a5c8b7d42",
      "approver": {
        "id": "4b3d92a7-5d8a-4c5e-87b1-2f6a3d8b9c42",
        "type": "USER_GROUP"
      },
      "line_number": 1,
      "purchase_receipt_data": {
        "quantity": 10.0,
        "lineNumber": 1,
        "unitAmount": 245.00,
        "orderNumber": "000087",
        "receiptNumber": "000045",
        "inventoryNumber": "PX-4015-72"
      }
    }
  ],
  "original_data_id": "d5728a4c-92f4-4e78-93b1-6d3a5c8b7d42"
}

```

## Original - Initial Lines / Fakturarader

```jsx
[
  {
    "id": "72d5a8c4-91f3-4b72-83d7-6a2c9f4b8d31",
    "creation_time": "2024-08-28 05:06:59.544851",
    "update_time": "2024-08-28 13:14:20.712003",
    "credit": null,
    "debit": 0.19,
    "invoiced_quantity": 0.0,
    "status": "APPROVED",
    "text": "Rounding Adjustment",
    "account_id": "c4b5728a-9f4d-47b2-83d1-6a5c8d7f31b2",
    "deferral_id": null,
    "deferral_code_id": null,
    "invoice_id": "5c21d8a3-b987-4a25-b0f3-4d92e7b6a512",
    "project_id": null,
    "project_task_id": null,
    "vat_code_id": "b21d5c8b-92f4-4e78-93b1-6d3a5c8b7d42",
    "approver": {
      "id": "a4d578c2-91f3-4b72-83d7-6a2c9f4b8d31",
      "type": "USER_GROUP"
    },
    "approver_to_visit": [],
    "applied_workflows": [],
    "line_action": null,
    "line_number": 2,
    "purchase_receipt_data": null,
    "original_data_id": "c5b42a8d-3f78-4e92-b1d7-6a9c5b7d8f31"
  },
  {
    "id": "d4b5728c-9f4d-47b2-83d1-6a5c8d7f31b2",
    "creation_time": "2024-08-28 05:06:59.543573",
    "update_time": "2024-08-28 13:14:20.710756",
    "credit": null,
    "debit": 3906.25,
    "invoiced_quantity": 0.0,
    "status": "APPROVED",
    "text": "High-Pressure Hose 1.5m",
    "account_id": "e4b5798c-21fd-4e72-9c3d-7b1a6d5c8f42",
    "deferral_id": null,
    "deferral_code_id": null,
    "invoice_id": "5c21d8a3-b987-4a25-b0f3-4d92e7b6a512",
    "project_id": null,
    "project_task_id": null,
    "vat_code_id": "b21d5c8b-92f4-4e78-93b1-6d3a5c8b7d42",
    "approver": {
      "id": "a4d578c2-91f3-4b72-83d7-6a2c9f4b8d31",
      "type": "USER_GROUP"
    },
    "approver_to_visit": [],
    "applied_workflows": [],
    "line_action": null,
    "line_number": 1,
    "purchase_receipt_data": {
      "quantity": 10.0,
      "lineNumber": 1,
      "unitAmount": 245.00,
      "orderNumber": "000087",
      "receiptNumber": "000045",
      "inventoryNumber": "PX-4015-72"
    },
    "original_data_id": "d5c42a8b-92f4-4e78-93b1-6d3a5c8b7d42"
  }
]

```

## Original - OriginalData

```jsx
{
  "id": "a1f3c7e5-9b42-4d6a-8d72-5c89b4f2d318",
  "creation_time": "2024-08-28 05:06:59.541257",
  "update_time": "2024-10-01 14:56:50.771475",
  "interpreted_data": {
    "id": "f3b1a5c7-8d42-4e7a-9b36-5c89b4d2f318",
    "ocr": "FAL-INV-20240827",
    "note": null,
    "type": "Invoice",
    "dueDate": "2024-09-26T00:00:00Z",
    "percent": "15",
    "vatAmount": 781.25,
    "supplierId": "8899456723",
    "invoiceDate": "2024-08-27T00:00:00Z",
    "currencyCode": "USD",
    "excVatAmount": 3125.00,
    "incVatAmount": 3906.25,
    "supplierName": "Orion Industrial Ltd",
    "invoiceNumber": "FAL-INV-20240827",
    "buyerReference": "7000004812",
    "orderReference": "FAL-20240828 - 000087",
    "organizationId": "7765432198",
    "roundingAmount": 0.0,
    "organizationName": "Falcon Logistics",
    "paymentMeansCode": "45",
    "supplierEndpointId": "8899456723",
    "supplierIdSchemeId": null,
    "salesOrderReference": "ORD789654",
    "supplierCountryCode": "US",
    "supplierVatIdentifier": "US889945672301",
    "organizationIdSchemeId": null,
    "payeeFinancialAccountId": "4567890",
    "financialInstitutionBranchId": "US:BANKWIRE"
  },
  "interpreted_xml": {
    "Invoice": {
      "@xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
      "cbc:ID": "FAL-INV-20240827",
      "cbc:DueDate": "2024-09-26",
      "cac:Delivery": {
        "cac:DeliveryParty": {
          "cac:PartyName": {
            "cbc:Name": "Falcon Logistics"
          }
        },
        "cac:DeliveryLocation": {
          "cbc:ID": "7765432198",
          "cac:Address": {
            "cac:Country": {
              "cbc:IdentificationCode": "US"
            },
            "cbc:CityName": "Springfield",
            "cbc:PostalZone": "67890",
            "cbc:StreetName": "Logistics Hub 12",
            "cac:AddressLine": {
              "cbc:Line": "Falcon Logistics"
            }
          }
        },
        "cbc:ActualDeliveryDate": "2024-08-27"
      },
      "cac:TaxTotal": {
        "cbc:TaxAmount": {
          "#text": "781.25",
          "@currencyID": "USD"
        },
        "cac:TaxSubtotal": [
          {
            "cbc:TaxAmount": {
              "#text": "781.25",
              "@currencyID": "USD"
            },
            "cac:TaxCategory": {
              "cbc:ID": "A",
              "cbc:Percent": "15",
              "cac:TaxScheme": {
                "cbc:ID": "VAT"
              }
            },
            "cbc:TaxableAmount": {
              "#text": "3125.00",
              "@currencyID": "USD"
            }
          },
          {
            "cbc:TaxAmount": {
              "#text": "0.00",
              "@currencyID": "USD"
            },
            "cac:TaxCategory": {
              "cbc:ID": "B",
              "cbc:Percent": "0",
              "cac:TaxScheme": {
                "cbc:ID": "VAT"
              }
            },
            "cbc:TaxableAmount": {
              "#text": "0.19",
              "@currencyID": "USD"
            }
          }
        ]
      },
      "cbc:IssueDate": "2024-08-27",
      "cbc:ProfileID": "urn:fdc:peppol.us:2024:poacc:billing:01:1.0",
      "cac:InvoiceLine": [
        {
          "cbc:ID": "50001",
          "cac:Item": {
            "cbc:Name": "High-Pressure Hose 1.5m",
            "cbc:Description": "Industrial-grade high-pressure hose",
            "cac:ClassifiedTaxCategory": {
              "cbc:ID": "A",
              "cbc:Percent": "15",
              "cac:TaxScheme": {
                "cbc:ID": "VAT"
              }
            },
            "cac:SellersItemIdentification": {
              "cbc:ID": "PX-4015-72"
            }
          },
          "cbc:Note": "Item",
          "cac:Price": {
            "cbc:PriceAmount": {
              "#text": "245.00",
              "@currencyID": "USD"
            },
            "cbc:BaseQuantity": {
              "#text": "1",
              "@unitCode": "EA"
            }
          },
          "cac:AllowanceCharge": {
            "cbc:Amount": {
              "#text": "50.00",
              "@currencyID": "USD"
            },
            "cbc:ChargeIndicator": "false",
            "cbc:AllowanceChargeReason": "Line Discount Amount"
          },
          "cbc:InvoicedQuantity": {
            "#text": "10",
            "@unitCode": "EA"
          },
          "cbc:LineExtensionAmount": {
            "#text": "3125.00",
            "@currencyID": "USD"
          }
        },
        {
          "cbc:ID": "50002",
          "cac:Item": {
            "cbc:Name": "Rounding Adjustment",
            "cac:ClassifiedTaxCategory": {
              "cbc:ID": "B",
              "cbc:Percent": "0",
              "cac:TaxScheme": {
                "cbc:ID": "VAT"
              }
            }
          },
          "cbc:Note": "Account Adjustment",
          "cac:Price": {
            "cbc:PriceAmount": {
              "#text": "0.19",
              "@currencyID": "USD"
            },
            "cbc:BaseQuantity": {
              "#text": "1",
              "@unitCode": "EA"
            }
          },
          "cbc:InvoicedQuantity": {
            "#text": "1",
            "@unitCode": "EA"
          },
          "cbc:LineExtensionAmount": {
            "#text": "0.19",
            "@currencyID": "USD"
          }
        }
      ],
      "cac:PaymentMeans": {
        "cbc:PaymentID": "FAL-INV-20240827",
        "cbc:PaymentMeansCode": "45",
        "cac:PayeeFinancialAccount": {
          "cbc:ID": "4567890",
          "cac:FinancialInstitutionBranch": {
            "cbc:ID": "US:BANKWIRE"
          }
        }
      },
      "cac:PaymentTerms": {
        "cbc:Note": "45 days net | Late fees apply"
      },
      "cbc:UBLVersionID": "2.1",
      "cac:OrderReference": {
        "cbc:ID": "FAL-20240828 - 000087",
        "cbc:SalesOrderID": "ORD789654"
      },
      "cbc:AccountingCost": "Falcon Logistics",
      "cbc:BuyerReference": "7000004812",
      "cbc:CustomizationID": "urn:cen.eu:en16931:2024#compliant#urn:fdc:peppol.us:2024:poacc:billing:3.0",
      "cbc:InvoiceTypeCode": "380",
      "cac:LegalMonetaryTotal": {
        "cbc:PayableAmount": {
          "#text": "3906.25",
          "@currencyID": "USD"
        },
        "cbc:TaxExclusiveAmount": {
          "#text": "3125.00",
          "@currencyID": "USD"
        },
        "cbc:TaxInclusiveAmount": {
          "#text": "3906.25",
          "@currencyID": "USD"
        },
        "cbc:LineExtensionAmount": {
          "#text": "3125.00",
          "@currencyID": "USD"
        },
        "cbc:AllowanceTotalAmount": {
          "#text": "0.00",
          "@currencyID": "USD"
        }
      },
      "cbc:DocumentCurrencyCode": "USD"
    }
  }
}

```