# -- Flights (optional master table)
# CREATE TABLE flights (
#   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#   callsign VARCHAR(20) NOT NULL,
#   airline VARCHAR(50),
#   flight_number VARCHAR(20),
#   aircraft_type VARCHAR(20),
#   origin VARCHAR(10),
#   destination VARCHAR(10),
#   scheduled_departure TIMESTAMP WITH TIME ZONE,
#   scheduled_arrival TIMESTAMP WITH TIME ZONE,
#   created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
# );

# -- Queue Requests (canonical persistent queue)
# CREATE TABLE queue_requests (
#   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#   flight_id UUID REFERENCES flights(id),
#   callsign VARCHAR(20),
#   request_type VARCHAR(10) NOT NULL, -- 'LANDING' or 'TAKEOFF'
#   priority_value BIGINT NOT NULL, -- -1 for MAYDAY else linux ms
#   score BIGINT NOT NULL, -- computed score (e.g., -1e12 or linux ms)
#   arrival_seq BIGINT NOT NULL, -- monotonic
#   state VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING/IN_PROGRESS/ASSIGNED/...
#   requested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
#   updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
#   metadata JSONB, -- e.g. position, eta, fuel state
#   assigned_assignment_id UUID, -- FK to runway_assignments when assigned
#   CONSTRAINT idx_queue_score_seq UNIQUE (score, arrival_seq)
# );

# CREATE INDEX idx_queue_requests_state_score ON queue_requests (state, score, arrival_seq);
# CREATE INDEX idx_queue_requests_callsign ON queue_requests (callsign);

# -- Runways
# CREATE TABLE runways (
#   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#   name VARCHAR(10) NOT NULL, -- e.g., '27L'
#   length_m INT,
#   heading DECIMAL(6,3),
#   active BOOLEAN DEFAULT TRUE,
#   created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
# );

# -- Runway Assignments (a schedule)
# CREATE TABLE runway_assignments (
#   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#   queue_request_id UUID REFERENCES queue_requests(id) UNIQUE,
#   runway_id UUID REFERENCES runways(id),
#   assigned_time TIMESTAMP WITH TIME ZONE NOT NULL, -- when clearance is scheduled
#   clearance_type VARCHAR(20), -- 'LINEUP_TAKEOFF', 'CLEARED_TO_LAND'
#   separation_seconds INT NOT NULL DEFAULT 0,
#   created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
#   created_by VARCHAR(50) -- agent/controller
# );

# CREATE INDEX idx_runway_assignments_runway_time ON runway_assignments (runway_id, assigned_time);

# # -- Separation rules
# # CREATE TABLE separation_rules (
# #   id SERIAL PRIMARY KEY,
# #   predecessor_wake VARCHAR(20) NOT NULL,
# #   follower_wake VARCHAR(20) NOT NULL,
# #   separation_seconds INT NOT NULL,
# #   effective_from TIMESTAMP WITH TIME ZONE DEFAULT now()
# # );only landing

# -- Events (audit)
# CREATE TABLE events (
#   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
#   queue_request_id UUID,
#   event_type VARCHAR(50),
#   payload JSONB,
#   created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
# );

# CREATE INDEX idx_events_qr ON events (queue_request_id);

# aircraft_types

# takeoff -> safety checks - > add to queue -> take off req -> approved takeoff
# landing req -> safety checks -> runway availability -> landing instructions

