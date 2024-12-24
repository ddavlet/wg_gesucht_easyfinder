# Flat Offers Collection Schema

This document describes the structure of documents in the `flat_offers` collection.

## Document Structure

```json
{
    "data_id": "string", // Unique identifier for the offer
    "link": "string", // URL to the original listing
    "is_active": "boolean", // Whether the offer is currently active
    "costs": {
    "rent": "string", // Base rent amount
    "additional_costs": "string", // Additional costs (Nebenkosten)
    "other_costs": "string", // Any other costs
    "deposit": "string", // Required deposit amount
    "transfer_agreement": "string", // Transfer agreement details
    "credit_check": "string" // Credit check requirements
    },
    "address": "string", // Property address
    "availability": {
    "available_from": "string", // Date when property becomes available
    "online": "string" // When the offer was posted online
    },
    "object_details": {
    "energy_efficiency_class": "string", // Energy rating
    "floor": "string", // Floor level
    "furnished": "string" // Furnishing status
    },
    "description": "string" // Full property description
}
```
## Field Descriptions

### Root Level Fields

- `data_id`: Unique identifier for the flat offer
- `link`: Direct URL to the original listing
- `is_active`: Boolean flag indicating if the offer is still available
- `address`: Complete address of the property
- `description`: Detailed description of the property

### Costs Object

Contains all financial information related to the property:

- `rent`: Base monthly rent
- `additional_costs`: Additional monthly costs (Nebenkosten)
- `other_costs`: Any other applicable costs
- `deposit`: Required security deposit
- `transfer_agreement`: Details about any transfer agreements
- `credit_check`: Information about credit check requirements

### Availability Object

Timing information:

- `available_from`: When the property becomes available for move-in
- `online`: Timestamp when the offer was posted

### Object Details

Physical characteristics of the property:

- `energy_efficiency_class`: Energy rating of the property
- `floor`: Floor level of the apartment
- `furnished`: Whether and how the property is furnished

## Validation

All documents in the collection are validated against this schema using the `validate_flat_offer()` function in `database.py`. Required fields are:

- data_id
- link
- is_active
- costs
- address
- availability
- object_details
- description
