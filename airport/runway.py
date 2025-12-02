class Runway:
    id: str
    name: str
    length_m: int
    heading: float
    active: bool = True
    # # Simple occupancy schedule: list of tuples (start_ms, end_ms)
    occupancy: List[Tuple[int, int]] = field(default_factory=list)

    def next_free_time(self, earliest_from_ms: int) -> int:
        """
        Given earliest_from_ms, compute earliest time runway is free >= earliest_from_ms.
        Simple model: occupancy intervals are non-overlapping and appended in chronological order.
        """
        if not self.occupancy:
            return earliest_from_ms
        # Find a gap or after last
        for start, end in self.occupancy:
            if earliest_from_ms < start:
                # earliest_from_ms is before this occupied block → free now
                return earliest_from_ms
            if start <= earliest_from_ms < end:
                # inside occupied block → free at end
                earliest_from_ms = end
                # continue checking next blocks
        return earliest_from_ms

    def reserve(self, start_ms: int, end_ms: int):
        """Reserve the runway for [start_ms, end_ms). Appends and keeps sorted."""
        # naive append & merge (for simplicity)
        self.occupancy.append((start_ms, end_ms))
        self.occupancy.sort()
        # merge overlapping intervals to keep occupancy tidy
        merged = []
        for s, e in self.occupancy:
            if not merged or s > merged[-1][1]:
                merged.append((s, e))
            else:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        self.occupancy = merged

    def release_past(self, now_ms: int):
        """Trim occupancy intervals that end before now_ms (cleanup)."""
        self.occupancy = [iv for iv in self.occupancy if iv[1] > now_ms]