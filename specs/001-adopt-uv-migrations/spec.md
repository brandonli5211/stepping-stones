# Feature Specification: Locked Backend Setup and Starting Schema

**Feature Branch**: `001-adopt-uv-migrations`

**Created**: 2026-10-27

**Status**: Draft (amended 2026-11-07 for Clean Architecture)

**Input**: User description: "we need to update the project to use UV and also introduce alembic for initial db table creation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One locked backend setup (Priority: P1)

A teammate gets a clean copy of the project and installs the backend
dependencies with one command. The versions they get are the versions
recorded for that copy of the project. The running application uses that
same recorded set. After install, the existing screen still shows that the
application is up and the database is reachable.

**Why this priority**: Today the backend installs from an unlocked list, and
the running application installs from that same loose list. Two people, or
a person and the running app, can end up with different versions. Nothing
else in this feature is trustworthy until there is one recorded set.

**Independent Test**: From a clean checkout, run the documented install,
start the application, and confirm the screen reports the database is
reachable. Compare the installed versions with the recorded set. They
match. Repeat from a second clean checkout of the same revision and get
the same versions.

**Acceptance Scenarios**:

1. **Given** a clean copy of the project, **When** a teammate runs the
   documented backend install, **Then** the install finishes from the
   recorded dependency set and does not require a second dependency list.
2. **Given** two clean installs of the same project revision, **When**
   both installs complete, **Then** both have the same dependency versions.
3. **Given** the recorded set and the declared dependencies disagree,
   **When** a teammate runs the install, **Then** the install fails with a
   clear error and does not silently choose other versions.
4. **Given** a successful install, **When** the teammate opens the
   application, **Then** the screen still reports that the application is
   up and the database is reachable.

---

### User Story 2 - A fresh database gets its starting schema (Priority: P2)

A teammate starts from an empty database. One documented step applies the
project's recorded schema history and leaves the database at the starting
schema. Running that step again does not fail and does not change the
schema. A new teammate with the same project revision gets the same
starting schema.

**Why this priority**: The database currently starts empty, and nothing in
the project records how tables are created. Later work needs one shared
history instead of tables created by hand.

**Independent Test**: Point the documented step at an empty database and
run it. Confirm the starting schema is present. Run it again and confirm
it finishes without error and the schema is unchanged. Repeat against a
second empty database from the same project revision and get the same
starting schema.

**Acceptance Scenarios**:

1. **Given** an empty database, **When** a teammate runs the documented
   schema step, **Then** the database matches the starting schema recorded
   in the project.
2. **Given** a database that is already at the starting schema, **When**
   the teammate runs the schema step again, **Then** the step finishes
   without error and the schema is unchanged.
3. **Given** two empty databases and the same project revision, **When**
   the schema step is applied to each, **Then** both databases end with
   the same starting schema.
4. **Given** the starting schema has been applied, **When** the teammate
   opens the application, **Then** the screen still reports that the
   application is up and the database is reachable.

### Edge Cases

- The database volume already exists from an earlier run and has no
  application tables. The schema step succeeds and leaves the starting
  schema in place. It does not wipe the database.
- Someone has created tables by hand that conflict with the starting
  schema. The schema step stops with a clear error and does not drop
  existing data.
- The recorded dependency set is missing. Install fails with a clear
  error instead of falling back to the old unlocked list.
- A teammate updates a declared dependency and forgets to update the
  recorded set. Install fails until the recorded set is updated.
- The schema step is interrupted after it has partially applied. A later
  run either finishes the starting schema or stops with a clear error. It
  does not leave a second, conflicting copy of the schema.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST record the exact backend dependency versions
  in one set that developers and the running application both use.
- **FR-002**: A developer MUST be able to install those backend
  dependencies with a single documented command from a clean copy of the
  project.
- **FR-003**: The running application MUST install from that recorded set.
  It MUST NOT keep a second, separate dependency list.
- **FR-004**: Installing or locking frontend dependencies MUST stay as it
  is today.
- **FR-005**: If the declared dependencies and the recorded set disagree,
  or the recorded set is missing, install MUST fail with a clear error
  rather than install different versions.
- **FR-006**: A fresh database MUST reach the starting schema by applying
  the project's recorded schema history. Creating those tables by hand
  MUST NOT be required.
- **FR-007**: The schema history MUST be stored in the project so every
  teammate on the same revision gets the same starting schema.
- **FR-008**: Applying the schema history to a database that is already at
  the starting schema MUST finish without error and MUST NOT change the
  schema.
- **FR-009**: A failed or repeated schema step MUST NOT drop existing
  data.
- **FR-010**: The starting schema MUST NOT include coaching records such
  as calls, templates, scores, or agents. Those tables are later work.
- **FR-011**: After a successful install and a successful schema step, the
  application MUST still report that it is up and that the database is
  reachable.
- **FR-012**: Every new function added for this feature MUST have an
  automated check in the same change. The check MUST call the function
  and assert its result or the failure it is specified to raise.
- **FR-013**: Feature behavior for health and the starting `app_meta`
  record MUST keep application rules separate from delivery and storage
  adapters. The HTTP health path MUST only report results produced by
  that application behavior. The starting-record rules (required unique
  key, required value) MUST be expressible without depending on a
  specific web framework or ORM.

### Key Entities

- **Dependency record**: The exact backend packages and versions for one
  revision of the project. Developers and the running application share
  it. It is not a second list of unpinned names.
- **Schema revision**: One ordered, recorded change to the database
  structure. Revisions are stored with the project and applied in order.
- **Starting schema**: The database state after the first revision has
  been applied to an empty database. For this feature that state is the
  schema history itself, not coaching data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A teammate with a clean copy of the project can install the
  backend dependencies and see the screen report a reachable database in
  one documented sequence, in under 10 minutes, not counting the
  first-time download of the base runtime.
- **SC-002**: Two clean installs from the same revision record identical
  dependency versions. A check of the two installs finds zero version
  differences.
- **SC-003**: On an empty database, the documented schema step finishes in
  one run. A second run finishes without error and a comparison shows no
  schema change.
- **SC-004**: Two empty databases prepared from the same revision match
  each other table for table.
- **SC-005**: After this work, the existing screen still shows that the
  application is up and the database is connected, with no new coaching
  screens required.
- **SC-006**: Every new function in the change has an automated check.
  Removing or breaking that function's specified behavior fails the check.
- **SC-007**: Health reporting and starting-record rules can be checked
  without standing up the HTTP server or the ORM session layer. Breaking
  the separation so those rules only exist inside the web route or the
  table mapping fails the automated checks for this feature.

## Assumptions

- The people affected are teammates setting up and running the project,
  not contact-centre agents. Agent-facing coaching behavior does not
  change.
- The request to change how the backend is installed means one locked
  install shared by developers and the running application, in place of
  today's unlocked list. The screen's own package install is out of scope.
- The application today only needs the database to accept a connection.
  It does not store calls, templates, scores, or agents. This feature
  does not design those tables.
- "Initial table creation" means a fresh database can be prepared by
  applying the recorded schema history. The starting schema is that
  history applied to an empty database. Product tables arrive with the
  features that need them, as further recorded revisions.
- Project rules already require recorded schema changes, one shared
  database, an automated check for every new function, and Clean
  Architecture for feature code. This feature does not relax those
  rules. It also does not, by itself, redesign unrelated existing code.
  Any file this feature edits still has to follow those rules.
- An existing local database that already has data is kept. The schema
  step must not wipe it.
