# TODO — Gong Call Chunker

_Last updated: 2026-02-27_

---

## Immediate Next Steps

- [ ] Add `user_email` (or `created_by`) column to the `calls` table and populate it from the JWT `email` claim on call creation — right now identity is verified but not persisted
- [ ] Add `GET /api/v1/me` endpoint that returns decoded JWT identity (email, name, picture) — lets the frontend display the logged-in user without a separate auth call
- [ ] Decide on `X-API-Key` path: keep it for script/programmatic access, or deprecate now that JWT is primary. Document the decision in CLAUDE.md.
- [ ] Update `scripts/seed_sample.py` to handle user-scoped calls once the `created_by` column exists

## Questions to Answer

- Do we want per-user call scoping (each user only sees their own calls) or org-wide visibility (any authenticated Google user sees all calls)?
- Should the schema editor be write-protected for non-admin users?
- Is Railway the permanent host, or is Vercel for the web layer still on the table?

## Dependencies / Blockers

- User-scoped calls blocked on the decision above about scoping model (per-user vs. org-wide)
- Nothing externally blocked right now

## Context for Next Session

**Where we left off:** Auth is fully working end-to-end. Google OAuth -> next-auth session -> proxy JWT -> backend verification. All 14 tests pass, build passes, deployed on Railway.

**Why we made key decisions:**
- Proxy route (not rewrites) so JWT signing stays server-side; browser never sees the JWT
- HS256 shared secret for simplicity in a single-tenant deployment
- 5-min JWT TTL because it's regenerated fresh on every request — no refresh logic needed

**Recommended starting point next session:** Add `user_email` to the calls model (small migration) and wire it up in the POST /calls and POST /calls/upload endpoints. That's the foundation for any user-scoped features.

---

## Completed

- [x] Google OAuth via next-auth
- [x] Next.js API proxy route with JWT injection
- [x] Backend JWT verification in api/auth.py
- [x] Railway deployment (both web and API services)
- [x] CORS / ALLOWED_ORIGINS configured on API
- [x] Security cleanup: debug endpoint removed
- [x] 14-test suite covering schema, parsing, chunker
- [x] YAML-driven extraction schema (no code changes to add new fields)
- [x] Claude tool-use structured extraction
- [x] Gong API sync integration
- [x] Analytics dashboard
- [x] Schema editor (visual + raw JSON)
