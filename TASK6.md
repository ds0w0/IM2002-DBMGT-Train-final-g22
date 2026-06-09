# TASK 6 EXTENSION: Promo Code & Discount Database Subsystem

This extension implements a fully production-grade Promotional Voucher and Discount tracking system entirely inside the relational database layer. (ds0w0)

## Motivation

Adding a promotional code subsystem provides significant commercial value to TransitFlow. It allows the system to support marketing campaigns, handle dynamic seasonal pricing, and enforce strict usage limitations (limits on maximum redemptions and validation of expiry windows) safely under high concurrency.

## Database Changes

We designed and engineered 1 new table and updated transactional checks:

1. `promo_codes`: Stores registered active discount vouchers, percentages, expiry policies, and a numeric atomic usage counter (`max_uses`, `current_uses`).

## Files Modified or Added

- `databases/relational/schema.sql`: Added the `promo_codes` schema layout and constraints.
- `databases/relational/queries.py`: Implemented full query functions with pessimistic row-locking (`FOR UPDATE`) for concurrent safety.

## Specific Functions Implemented

- `query_validate_promo_code(code)`: Read-only endpoint to verify code existence, validity, expiry, and capacity.
- `execute_booking_with_promo(...)`: Atomic write operation wrapping code verification, dynamic price reduction, seat protection, and voucher increment tracking in a single database transaction transaction.
