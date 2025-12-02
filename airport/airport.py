# # class AirPortContols:
# #     def __init__(self):
# #         pass

# #     def landing():
# #         pass

# #     def take_off():
# #         pass

# class AirportFloorPlan(metaclass=SingletonMeta):
#     """
#     Singleton that models the airport floor plan and performs runway allocation.
#     """

#     # VERY_NEGATIVE used as score for emergencies
#     VERY_NEGATIVE = -10**18

#     def __init__(self, airport_code: str):
#         self.airport_code = airport_code
#         self.runways: Dict[str, Runway] = {}
#         self.lock = threading.RLock()
#         # priority heap: elements are (score, arrival_seq, Request)
#         self._pq: List[Tuple[int, int, Request]] = []
#         self._seq = itertools.count(start=1)
#         # mapping request_id -> tuple(score, seq, Request) for quick updates (optional)
#         self._pending_map: Dict[str, Tuple[int, int, Request]] = {}
#         # separation rules (predecessor_wake, follower_wake) -> seconds
#         # default example values (configurable)
#         self.separation_rules: Dict[Tuple[str, str], int] = {
#             ('HEAVY', 'HEAVY'): 120,
#             ('HEAVY', 'MEDIUM'): 120,
#             ('HEAVY', 'LIGHT'): 120,
#             ('MEDIUM', 'HEAVY'): 90,
#             ('MEDIUM', 'MEDIUM'): 90,
#             ('MEDIUM', 'LIGHT'): 60,
#             ('LIGHT', 'HEAVY'): 60,
#             ('LIGHT', 'MEDIUM'): 60,
#             ('LIGHT', 'LIGHT'): 60,
#         }
#         # assignments active
#         self.assignments: Dict[str, Assignment] = {}

#     # ---- Runway management ----
#     def add_runway(self, name: str, length_m: int, heading: float) -> str:
#         with self.lock:
#             rid = str(uuid.uuid4())
#             rv = Runway(id=rid, name=name, length_m=length_m, heading=heading)
#             self.runways[rid] = rv
#             return rid

#     def get_runways(self) -> List[Runway]:
#         with self.lock:
#             return list(self.runways.values())

#     # ---- Priority queue handling ----
#     def push_request(self, callsign: str, req_type: str, aircraft_wake: str,
#                      eta_ms: Optional[int], mayday: bool=False, metadata: Optional[dict]=None) -> str:
#         """
#         Add a request to the priority queue.
#         mayday: bool → if True priority_value is -1 (highest).
#         Returns request_id.
#         """
#         with self.lock:
#             rid = str(uuid.uuid4())
#             priority_value = -1 if mayday else (eta_ms if eta_ms is not None else millis())
#             # score mapping: MAYDAY -> VERY_NEGATIVE else use priority_value (ms)
#             score = self.VERY_NEGATIVE if priority_value == -1 else priority_value
#             seq = next(self._seq)
#             req = Request(request_id=rid, callsign=callsign, req_type=req_type,
#                           aircraft_wake=aircraft_wake, eta_ms=eta_ms,
#                           priority_value=priority_value, metadata=metadata or {})
#             heapq.heappush(self._pq, (score, seq, req))
#             self._pending_map[rid] = (score, seq, req)
#             return rid

#     def mark_mayday(self, request_id: str):
#         """
#         Convert an existing pending request to MAYDAY (highest priority).
#         If it's not pending, returns False.
#         """
#         with self.lock:
#             entry = self._pending_map.get(request_id)
#             if not entry:
#                 return False
#             _, _, req = entry
#             # remove old entry lazily by marking and pushing a new one;
#             # simplest approach: push new MAYDAY entry and mark old as invalid by deleting from map
#             # but to avoid duplicates in pq we remove from map and push new
#             del self._pending_map[request_id]
#             # push new
#             return self._push_mayday_existing(req)

#     def _push_mayday_existing(self, req: Request):
#         # reuse same request id
#         req.priority_value = -1
#         score = self.VERY_NEGATIVE
#         seq = next(self._seq)
#         with self.lock:
#             heapq.heappush(self._pq, (score, seq, req))
#             self._pending_map[req.request_id] = (score, seq, req)
#         return True

#     def _pop_pending(self) -> Optional[Request]:
#         """
#         Pop next pending request from heap, skipping stale/removed entries.
#         """
#         with self.lock:
#             while self._pq:
#                 score, seq, req = heapq.heappop(self._pq)
#                 mapped = self._pending_map.get(req.request_id)
#                 # check that this is the active entry for that request
#                 if mapped and mapped[0] == score and mapped[1] == seq:
#                     del self._pending_map[req.request_id]
#                     return req
#                 # otherwise it's stale; continue popping
#             return None

#     # ---- Allocation logic ----
#     def allocate_next(self, now_ms: Optional[int] = None) -> Optional[Assignment]:
#         """
#         Pop the next request and allocate a runway for it based on separation rules.
#         Returns Assignment or None if no pending requests or no feasible runway.
#         """
#         now_ms = now_ms or millis()
#         with self.lock:
#             # cleanup runway occupancy past now
#             for r in self.runways.values():
#                 r.release_past(now_ms)

#             req = self._pop_pending()
#             if not req:
#                 return None

#             # Evaluate each runway for earliest feasible assigned_time (ms)
#             best_runway: Optional[Runway] = None
#             best_assigned_time: Optional[int] = None
#             for runway in self.runways.values():
#                 if not runway.active:
#                     continue
#                 earliest_candidate = max(now_ms, req.eta_ms or now_ms)
#                 # find next free time on runway >= earliest_candidate
#                 runway_next_free = runway.next_free_time(earliest_candidate)
#                 # find the last assignment on the runway to compute separation
#                 # we approximate: separation applies relative to runway occupancy end last
#                 last_end = runway_next_free  # runway_next_free already considers occupancy
#                 # To compute separation seconds we need predecessor wake; find most recent occupancy predecessor wake
#                 # For simplicity assume separation computed against last occupancy entry's associated aircraft
#                 # -> We don't store predecessor wake per occupancy in this simplified model.
#                 # Instead, apply a conservative max separation across all wake combos for safety:
#                 max_sep_seconds = max(self.separation_rules.values()) if self.separation_rules else 60
#                 candidate_time = last_end + max_sep_seconds * 1000
#                 # allow immediate if runway_next_free == earliest_candidate (i.e., no active occupancy) then candidate_time is earliest + sep
#                 # Choose assignment time that respects separation but minimize delay
#                 if best_assigned_time is None or candidate_time < best_assigned_time:
#                     best_assigned_time = candidate_time
#                     best_runway = runway

#             if best_runway is None or best_assigned_time is None:
#                 # no runway available
#                 return None

#             # Reserve runway: decide occupancy window length: simple constant occupancy depending on type
#             occupancy_seconds = 60 if req.req_type == 'TAKEOFF' else 90  # simple heuristic
#             start_ms = best_assigned_time
#             end_ms = start_ms + occupancy_seconds * 1000
#             best_runway.reserve(start_ms, end_ms)

#             # Create assignment
#             assignment = Assignment(
#                 assignment_id=str(uuid.uuid4()),
#                 request_id=req.request_id,
#                 runway_id=best_runway.id,
#                 assigned_time_ms=start_ms,
#                 clearance_type=('CLEARED_TO_LAND' if req.req_type == 'LAND' else 'CLEARED_TAKEOFF'),
#                 created_at_ms=millis()
#             )
#             self.assignments[assignment.assignment_id] = assignment
#             return assignment

#     def release_assignment(self, assignment_id: str):
#         """Release assignment (remove from active assignments). This does not remove occupancy history."""
#         with self.lock:
#             if assignment_id in self.assignments:
#                 del self.assignments[assignment_id]
#                 return True
#             return False

#     # ---- Observability / Helpers ----
#     def peek_pending(self, limit: int = 10) -> List[Request]:
#         """Return up to `limit` pending requests in priority order (destructive peek not performed)."""
#         with self.lock:
#             # Make a shallow copy of heap, pop up to limit, then discard
#             tmp = list(self._pq)
#             heapq.heapify(tmp)
#             out = []
#             while tmp and len(out) < limit:
#                 score, seq, req = heapq.heappop(tmp)
#                 mapped = self._pending_map.get(req.request_id)
#                 if mapped and mapped[0] == score and mapped[1] == seq:
#                     out.append(req)
#             return out

#     def status(self) -> dict:
#         with self.lock:
#             now = millis()
#             runways = [{
#                 'id': r.id, 'name': r.name, 'length_m': r.length_m, 'heading': r.heading,
#                 'active': r.active, 'occupancy': r.occupancy
#             } for r in self.runways.values()]
#             pending_count = len(self._pending_map)
#             return {
#                 'airport_code': self.airport_code,
#                 'now_ms': now,
#                 'runways': runways,
#                 'pending_requests': pending_count,
#                 'active_assignments': len(self.assignments)
#             }